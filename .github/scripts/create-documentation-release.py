"""
Code to update the production branch's documentation

This does not update the development branches code documentation.
"""

import requests
import json
import sys

OWNER = "osg-htc"
REPO = "path-portal"


class Tag:

    def __init__(self, tag: str, **kwargs):
        self.tag_string = tag

        for key, value in kwargs.items():
            setattr(self, key, value)

    @property
    def decomposed_tag(self) -> list:
        """Tag as list of Principal Components"""
        return self.tag_string[1:].split(".")

    @decomposed_tag.setter
    def decomposed_tag(self, value):
        self.tag_string = f"v{'.'.join(value)}"

    @property
    def standardized_tag(self):
        standardized_tag = self.decomposed_tag + [""] * (6 - len(self.decomposed_tag))  # Standardize list length
        standardized_tag = [x.zfill(10) for x in standardized_tag]                            # Standardize composition
        standardized_tag = ".".join(standardized_tag)                                         # Convert to string
        return standardized_tag

    def __str__(self):
        return self.tag_string

    def __eq__(self, other):
        return self.tag_string == other.tag_string

    def __gt__(self, other):
        return self.standardized_tag > other.standardized_tag

    def __lt__(self, other):
        return not self.__gt__(other)

    def is_itb(self):
        return 'itb' in self.tag_string

    def has_doc_tag(self):
        """Check if doc indicator is in the tag"""
        if self.is_itb():
            return len(self.decomposed_tag) == 5  # based on vX.Y.Z.itb.W standard
        else:
            return len(self.decomposed_tag) == 3  # based on vX.Y.Z standard

    def increment_doc_tag(self):
        """Increment the doc indicator of the tag string"""
        if self.has_doc_tag():
            self.decomposed_tag = self.decomposed_tag + ['1']  # if there isn't one, add it
        else:
            self.decomposed_tag = self.decomposed_tag[:-1] + [str(int(self.decomposed_tag[-1]) + 1)]


def create_release(tag: str, token: str):
    api_endpoint = f"https://api.github.com/repos/{OWNER}/{REPO}/releases"

    data = {
        "tag_name": tag,
        "name": "Documentation Release",
        "message": "This is a automated release resulting from a update to the documentation website",
    }

    authorization_header = {
        "Authorization": f"token {token}"
    }

    response = requests.post(api_endpoint, headers=authorization_header, data=json.dumps(data))

    if response.ok:
        print(tag, end="")  # Need the tag so that we can use it in following workflows


def get_tags() -> list:
    api_url = f"https://api.github.com/repos/{OWNER}/{REPO}/tags"

    query_parameters = {
        "per_page": "100"
    }

    response = requests.get(api_url, data=query_parameters)
    tags = response.json()

    return tags


def get_most_recent_production_tag(tags: list):
    tags = [Tag(tag['name'], **tag) for tag in tags]

    prod_tags = filter(lambda tag: not tag.is_itb(), tags)

    most_recent_production_tag = max(prod_tags)

    return most_recent_production_tag


def get_incremented_release_tag(tags: list):

    most_recent_production_tag = get_most_recent_production_tag(tags)

    most_recent_production_tag.increment_doc_tag()

    return most_recent_production_tag


def create_updated_documentation_release(token):
    tags = get_tags()
    most_recent_production_tag = get_most_recent_production_tag(tags)
    create_release(str(most_recent_production_tag), token)


if __name__ == "__main__":
    gh_token = sys.argv[1]
    create_updated_documentation_release(gh_token)
