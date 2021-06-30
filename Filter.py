from json import loads
from re import compile, error, Match, IGNORECASE


def concat_generators(*args):
    for gen in args:
        yield from gen


class Filter:
    def __init__(self, cluster_obj, patterns, match_against, size):
        self.cluster_obj = cluster_obj
        self.patterns = patterns
        self.match_against = match_against
        self.size = size

        # Does regex match?
        self.pattern_match = None
        # Does size match?
        self.size_match = None
        # A list of documents/databases names that matches the supplied regex patterns
        self.matches = []

        self.main()

    def get_size(self):
        self.size = loads(self.size)

    def read_gen(self):
        with open(self.patterns, "r") as f:
            yield from f

    def pattern_gen(self):
        for pattern in self.read_gen():
            yield self.valid_regex(pattern.strip().replace("\\", "\\\\"))

    @staticmethod
    def valid_regex(pattern):
        try:
            return compile(pattern)
        except error:
            # Exit or log to file
            pass

    def match_against_manager(self):
        if self.match_against:
            if self.match_against == "Databases names":
                return self.cluster_obj.database_names_gen
            elif self.match_against == "Document names":
                return self.cluster_obj.collections_names_gen_list
            else:
                return concat_generators(self.cluster_obj.database_names_gen,
                                         self.cluster_obj.collections_names_gen_list)

    def match_regex(self):
        if self.patterns:
            match_against_gen = self.match_against_manager()
            for text in match_against_gen:
                for pattern in self.pattern_gen():
                    if isinstance(pattern.search(text, IGNORECASE), Match):
                        self.matches.append(text)
                        self.pattern_match = True
            # If  self.pattern_match didn't change it didn't match
            if not self.pattern_match:
                self.pattern_match = False

    def filter_size(self):
        if self.size:
            self.get_size()
            if self.size.get("bigger"):
                if self.cluster_obj.cluster_size > self.size.get("bigger"):
                    self.size_match = True
            elif self.size.get("smaller"):
                if self.cluster_obj.cluster_size < self.size.get("smaller"):
                    self.size_match = True
            elif all((self.size.get("bigger"), self.size.get("smaller"))):
                if self.size.get("bigger") >= self.cluster_obj.cluster_size >= self.size.get("smaller"):
                    self.size_match = True

    def main(self):
        self.match_regex()
        self.filter_size()
