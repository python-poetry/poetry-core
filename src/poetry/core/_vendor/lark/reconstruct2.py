from collections import defaultdict

from .tree import Tree
from .visitors import Transformer_InPlace
from .common import ParserConf
from .lexer import Token, PatternStr
from .parsers import earley
from .grammar import Rule, Terminal, NonTerminal



def is_discarded_terminal(t):
    return t.is_term and t.filter_out

def is_iter_empty(i):
    try:
        _ = next(i)
        return False
    except StopIteration:
        return True

class WriteTokensTransformer(Transformer_InPlace):
    def __init__(self, tokens):
        self.tokens = tokens

    def __default__(self, data, children, meta):
        #  if not isinstance(t, MatchTree):
            #  return t
        if not getattr(meta, 'match_tree', False):
            return Tree(data, children)

        iter_args = iter(children)
        print('@@@', children, meta.orig_expansion)
        to_write = []
        for sym in meta.orig_expansion:
            if is_discarded_terminal(sym):
                t = self.tokens[sym.name]
                value = t.pattern.value
                if not isinstance(t.pattern, PatternStr):
                    if t.name == "_NEWLINE":
                        value = "\n"
                    else:
                        raise NotImplementedError("Reconstructing regexps not supported yet: %s" % t)
                to_write.append(value)
            else:
                x = next(iter_args)
                if isinstance(x, list):
                    to_write += x
                else:
                    if isinstance(x, Token):
                        assert Terminal(x.type) == sym, x
                    else:
                        assert NonTerminal(x.data) == sym, (sym, x)
                    to_write.append(x)

        assert is_iter_empty(iter_args)
        return to_write


class MatchTree(Tree):
    pass

class MakeMatchTree:
    def __init__(self, name, expansion):
        self.name = name
        self.expansion = expansion

    def __call__(self, args):
        t = MatchTree(self.name, args)
        t.meta.match_tree = True
        t.meta.orig_expansion = self.expansion
        return t

from lark.load_grammar import SimplifyRule_Visitor, RuleTreeToText
class Reconstructor:
    def __init__(self, parser):
        # XXX TODO calling compile twice returns different results!
        assert parser.options.maybe_placeholders == False
        tokens, rules, _grammar_extra = parser.grammar.compile(parser.options.start)

        self.write_tokens = WriteTokensTransformer({t.name:t for t in tokens})
        self.rules = list(set(list(self._build_recons_rules(rules))))
        callbacks = {rule: rule.alias for rule in self.rules}   # TODO pass callbacks through dict, instead of alias?
        for r in self.rules:
            print("*", r)
        self.parser = earley.Parser(ParserConf(self.rules, callbacks, parser.options.start),
                                    self._match, resolve_ambiguity=True)

    def _build_recons_rules(self, rules):
        expand1s = {r.origin for r in rules if r.options.expand1}

        aliases = defaultdict(list)
        for r in rules:
            if r.alias:
                aliases[r.origin].append( r.alias )

        rule_names = {r.origin for r in rules}
        nonterminals = {sym for sym in rule_names
                       if sym.name.startswith('_') or sym in expand1s or sym in aliases }

        for r in rules:
            _recons_exp = []
            for sym in r.expansion:
                if not is_discarded_terminal(sym):
                    if sym in nonterminals:
                        if sym in expand1s:
                            v = Tree('expansions', [sym, Terminal(sym.name.upper())])
                        else:
                            v = sym
                    else:
                        v = Terminal(sym.name.upper())
                    _recons_exp.append(v)

            simplify_rule = SimplifyRule_Visitor()
            rule_tree_to_text = RuleTreeToText()
            tree = Tree('expansions', [Tree('expansion', _recons_exp)])
            simplify_rule.visit(tree)
            expansions = rule_tree_to_text.transform(tree)

            for recons_exp, alias in expansions:

                # Skip self-recursive constructs
                if recons_exp == [r.origin]:
                    continue

                sym = NonTerminal(r.alias) if r.alias else r.origin

                yield Rule(sym, recons_exp, alias=MakeMatchTree(sym.name, r.expansion))

        for origin, rule_aliases in aliases.items():
            for alias in rule_aliases:
                yield Rule(origin, [Terminal(alias.upper())], alias=MakeMatchTree(origin.name, [NonTerminal(alias)]))
            yield Rule(origin, [Terminal(origin.name.upper())], alias=MakeMatchTree(origin.name, [origin]))

    def _match(self, term, token):
        if isinstance(token, Tree):
            return Terminal(token.data.upper()) == term
        elif isinstance(token, Token):
            return term == Terminal(token.type.upper())
        assert False

    def _reconstruct(self, tree):
        # TODO: ambiguity?
        unreduced_tree = self.parser.parse(tree.children, tree.data)   # find a full derivation
        assert unreduced_tree.data == tree.data
        res = self.write_tokens.transform(unreduced_tree)
        for item in res:
            if isinstance(item, Tree):
                for x in self._reconstruct(item):
                    yield x
            else:
                yield item

    def reconstruct(self, tree):
        return ''.join(self._reconstruct(tree))
