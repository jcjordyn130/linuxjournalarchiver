# linuxjournalarchiver - Some hacky code I wrote to archive the Linux Journal.
# Licensed under the BSD-3-Clause license.
from bs4 import BeautifulSoup
import requests
import re
import pathlib

# Download the download page.
print("Downloading magazine list...")
session = requests.session()

# Update the User Agent to curl, this is because the server-side code
# handles curl specially.
session.headers.update({"User-Agent": "curl/7.65.3"})

r = session.get("https://secure2.linuxjournal.com/pdf/dljdownload.php")
soup = BeautifulSoup(r.text, "lxml")

# Process all the download buttons.
for e in reversed(soup.find_all("div", class_ = "downloadbtn")):
    # Some issues don't have certain file formats, skip these.
    if e.get_text() == "N/A":
        print("No link")
        continue

    # Certain downloadbtn div elements don't have a link, skip these.
    try:
        link = e.a.get("href")
    except AttributeError:
        print("Invalid element")
        continue

    # Download the magazine.
    magr = session.get(link + '&action=spit', stream = True)

    # Get the name and format it.
    name = re.findall(r'filename=(.+)', magr.headers["Content-Disposition"])
    name = name[0].strip('"')

    # Special treatment for Supplemental issues.
    if not "Supplement" in link:
        # Get the date.
        date = re.findall("....-..(?=\....)", name)[0]
        year, month = date.split("-")

        # Get the path.
        dirpath = pathlib.Path(f"{year}/{month}")
        dirpath.mkdir(parents = True, exist_ok = True)
        magpath = dirpath / name
    else:
        # We don't have a date,
        # so we use the "Supplement" folder as a fill in on suplemental issues.
        dirpath = pathlib.Path(f"Supplement")
        dirpath.mkdir(parents = True, exist_ok = True)
        magpath = dirpath / name

    # Don't download a magazine that we have already downloaded.
    if magpath.exists():
        print(f"{magpath} exists... skipping")
        continue

    # Debug printing.
    print(f"Downloading {link} to {magpath}...")

    # Save the data to a file.
    with open(f"{magpath}", "wb") as f:
        bytesdownloaded = 0

        for chunk in magr.iter_content(chunk_size = 8192):
            if chunk: # filter out keep-alive new chunks
                bytesdownloaded+=len(chunk)
                print(f"{name}: {bytesdownloaded}/{magr.headers['Content-Length']}")
                f.write(chunk)