import posixpath
import re
import urllib.parse as urlparse

from typing import Any
from typing import Optional
from typing import Tuple

from .utils import path_to_url
from .utils import splitext


class Link:
    def __init__(
        self,
        url: str,
        comes_from: Optional[Any] = None,
        requires_python: Optional[str] = None,
    ) -> None:
        """
        Object representing a parsed link from https://pypi.python.org/simple/*

        url:
            url of the resource pointed to (href of the link)
        comes_from:
            instance of HTMLPage where the link was found, or string.
        requires_python:
            String containing the `Requires-Python` metadata field, specified
            in PEP 345. This may be specified by a data-requires-python
            attribute in the HTML link tag, as described in PEP 503.
        """

        # url can be a UNC windows share
        if url.startswith("\\\\"):
            url = path_to_url(url)

        self.url = url
        self.comes_from = comes_from
        self.requires_python = requires_python if requires_python else None

    def __str__(self) -> str:
        if self.requires_python:
            rp = " (requires-python:%s)" % self.requires_python
        else:
            rp = ""
        if self.comes_from:
            return "%s (from %s)%s" % (self.url, self.comes_from, rp)
        else:
            return str(self.url)

    def __repr__(self) -> str:
        return "<Link %s>" % self

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, Link):
            return NotImplemented
        return self.url == other.url

    def __ne__(self, other: Any) -> bool:
        if not isinstance(other, Link):
            return NotImplemented
        return self.url != other.url

    def __lt__(self, other: Any) -> bool:
        if not isinstance(other, Link):
            return NotImplemented
        return self.url < other.url

    def __le__(self, other: Any) -> bool:
        if not isinstance(other, Link):
            return NotImplemented
        return self.url <= other.url

    def __gt__(self, other: Any) -> bool:
        if not isinstance(other, Link):
            return NotImplemented
        return self.url > other.url

    def __ge__(self, other: Any) -> bool:
        if not isinstance(other, Link):
            return NotImplemented
        return self.url >= other.url

    def __hash__(self) -> int:
        return hash(self.url)

    @property
    def filename(self) -> str:
        _, netloc, path, _, _ = urlparse.urlsplit(self.url)
        name = posixpath.basename(path.rstrip("/")) or netloc
        name = urlparse.unquote(name)

        return name

    @property
    def scheme(self) -> str:
        return urlparse.urlsplit(self.url)[0]

    @property
    def netloc(self) -> str:
        return urlparse.urlsplit(self.url)[1]

    @property
    def path(self) -> str:
        return urlparse.unquote(urlparse.urlsplit(self.url)[2])

    def splitext(self) -> Tuple[str, str]:
        return splitext(posixpath.basename(self.path.rstrip("/")))

    @property
    def ext(self) -> str:
        return self.splitext()[1]

    @property
    def url_without_fragment(self) -> str:
        scheme, netloc, path, query, fragment = urlparse.urlsplit(self.url)
        return urlparse.urlunsplit((scheme, netloc, path, query, None))

    _egg_fragment_re = re.compile(r"[#&]egg=([^&]*)")

    @property
    def egg_fragment(self) -> Optional[str]:
        match = self._egg_fragment_re.search(self.url)
        if not match:
            return None
        return match.group(1)

    _subdirectory_fragment_re = re.compile(r"[#&]subdirectory=([^&]*)")

    @property
    def subdirectory_fragment(self) -> Optional[str]:
        match = self._subdirectory_fragment_re.search(self.url)
        if not match:
            return None
        return match.group(1)

    _hash_re = re.compile(r"(sha1|sha224|sha384|sha256|sha512|md5)=([a-f0-9]+)")

    @property
    def hash(self) -> Optional[str]:
        match = self._hash_re.search(self.url)
        if match:
            return match.group(2)
        return None

    @property
    def hash_name(self) -> Optional[str]:
        match = self._hash_re.search(self.url)
        if match:
            return match.group(1)
        return None

    @property
    def show_url(self) -> str:
        return posixpath.basename(self.url.split("#", 1)[0].split("?", 1)[0])

    @property
    def is_wheel(self) -> bool:
        return self.ext == ".whl"

    @property
    def is_wininst(self) -> bool:
        return self.ext == ".exe"

    @property
    def is_egg(self) -> bool:
        return self.ext == ".egg"

    @property
    def is_sdist(self) -> bool:
        return self.ext in {".tar.bz2", ".tar.gz", ".zip"}

    @property
    def is_artifact(self) -> bool:
        """
        Determines if this points to an actual artifact (e.g. a tarball) or if
        it points to an "abstract" thing like a path or a VCS location.
        """
        if self.scheme in ["ssh", "git", "hg", "bzr", "sftp", "svn"]:
            return False

        return True
