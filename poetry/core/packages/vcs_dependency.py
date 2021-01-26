from typing import List
from typing import Set
from typing import Union
from warnings import warn

from poetry.core.vcs import git

from .dependency import Dependency


class VCSDependency(Dependency):
    """
    Represents a VCS dependency
    """

    def __init__(
        self,
        name,
        vcs,
        source,
        branch=None,
        tag=None,
        rev=None,
        resolved_rev=None,
        category="main",
        optional=False,
        editable=False,
        develop=False,
        extras=None,  # type: Union[List[str], Set[str]]
    ):
        self._vcs = vcs
        self._source = source

        if not any([branch, tag, rev]):
            # If nothing has been specified, we assume master
            branch = "master"

        self._branch = branch
        self._tag = tag
        self._rev = rev
        # TODO: Remove the following once poetry has been updated to use editable in source.
        if develop:
            if editable:
                raise ValueError(
                    'Deprecated "develop" parameter may not be passed with new "editable" parameter. '
                    'Only use "editable"!'
                )
            warn(
                '"develop" parameter is deprecated, use "editable" instead.',
                DeprecationWarning,
            )
        self._editable = editable

        super(VCSDependency, self).__init__(
            name,
            "*",
            category=category,
            optional=optional,
            allows_prereleases=True,
            source_type=self._vcs.lower(),
            source_url=self._source,
            source_reference=branch or tag or rev,
            source_resolved_reference=resolved_rev,
            extras=extras,
        )

    @property
    def vcs(self):
        return self._vcs

    @property
    def source(self):
        return self._source

    @property
    def branch(self):
        return self._branch

    @property
    def tag(self):
        return self._tag

    @property
    def rev(self):
        return self._rev

    @property
    def editable(self):  # type: () -> bool
        return self._editable

    # TODO: Remove the following once poetry has been updated to use editable in source.
    @property
    def develop(self):  # type: () -> bool
        warn(
            '"develop" property is deprecated, use "editable" instead.',
            DeprecationWarning,
        )
        return self.editable

    @property
    def reference(self):  # type: () -> str
        return self._branch or self._tag or self._rev

    @property
    def pretty_constraint(self):  # type: () -> str
        if self._branch:
            what = "branch"
            version = self._branch
        elif self._tag:
            what = "tag"
            version = self._tag
        else:
            what = "rev"
            version = self._rev

        return "{} {}".format(what, version)

    @property
    def base_pep_508_name(self):  # type: () -> str
        requirement = self.pretty_name
        parsed_url = git.ParsedUrl.parse(self._source)

        if self.extras:
            requirement += "[{}]".format(",".join(self.extras))

        if parsed_url.protocol is not None:
            requirement += " @ {}+{}@{}".format(self._vcs, self._source, self.reference)
        else:
            requirement += " @ {}+ssh://{}@{}".format(
                self._vcs, parsed_url.format(), self.reference
            )

        return requirement

    def is_vcs(self):  # type: () -> bool
        return True

    def accepts_prereleases(self):  # type: () -> bool
        return True

    def with_constraint(self, constraint):
        new = VCSDependency(
            self.pretty_name,
            self._vcs,
            self._source,
            branch=self._branch,
            tag=self._tag,
            rev=self._rev,
            resolved_rev=self._source_resolved_reference,
            optional=self.is_optional(),
            category=self.category,
            editable=self._editable,
            extras=self._extras,
        )

        new._constraint = constraint
        new._pretty_constraint = str(constraint)

        new.is_root = self.is_root
        new.python_versions = self.python_versions
        new.marker = self.marker
        new.transitive_marker = self.transitive_marker

        for in_extra in self.in_extras:
            new.in_extras.append(in_extra)

        return new

    def __str__(self):
        reference = self._vcs
        if self._branch:
            reference += " branch {}".format(self._branch)
        elif self._tag:
            reference += " tag {}".format(self._tag)
        elif self._rev:
            reference += " rev {}".format(self._rev)

        return "{} ({} {})".format(self._pretty_name, self._constraint, reference)

    def __hash__(self):
        return hash((self._name, self._vcs, self._branch, self._tag, self._rev))
