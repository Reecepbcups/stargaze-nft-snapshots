import json
import os

from helpers import CompactJSONEncoder

# Call this only to perform mass formatting for all the JSON files.


PROJECTS = [
    "badkids",
    "bitkids",
    "celestine_sloth_society",
    "racoon",
    "cryptoniummaker",
    "afterthefilter",
    "pixelsquids",
    "sneaky",
    "geckies",
    "rektbulls",
]


def main():
    curr_dir = os.path.dirname(os.path.realpath(__file__))

    for project in PROJECTS:

        directory = os.path.join(curr_dir, f"{project}")
        if not os.path.exists(directory):
            exit(f"directory {directory} does not exist")

        files = os.listdir(directory)

        for file in files:

            fp = os.path.join(directory, file)

            with open(fp, "r") as f:
                data = json.load(f)

            holders = data.get("holders", {})
            data["holders"] = {
                k: v
                for k, v in sorted(
                    holders.items(), key=lambda item: len(item[1]), reverse=True
                )
            }

            print(f"Processing {fp}...")

            # save data back to file with the cls CompactJSONEncoder
            with open(fp, "w") as f:
                json.dump(data, f, cls=CompactJSONEncoder, indent=4)

    pass


if __name__ == "__main__":
    main()
