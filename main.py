from __future__ import annotations

import glob
import os
import re
import pickle
import xml.etree.ElementTree as ET
from tqdm import tqdm
from PIL import Image
import pandas as pd
import streamlit as st
from src.data import oclc

LOAD_XMLS = False
LOAD_PICKLE = True

smark_regex = re.compile("[0-9]{1,5}[\s\.]{1,2}[\w]{1,3}[\s\.]{1,2}[\w0-9]{1,5}")
author_regex = re.compile("[A-Z]+[\s]+\([A-Z][a-z]+\)")
isbn_regex = re.compile("ISBN\s[0-9\-\s]+")

def extractLines(root: ET.Element):
    lines = []

    textRegions = [x for x in root[1] if len(x) > 2]  # Empty Text Regions Removed

    for textRegion in textRegions:
        textLines = textRegion[1:-1]  # Skip coordinate data in first child
        for textLine in textLines:
            lines.append(textLine[-1][0].text)  # Text equivalent for line
    return lines


def extractLinesForVol(vol: list[ET.Element]):
    allLines = []
    for root in tqdm(vol):
        rootLines = extractLines(root)
        allLines.append(rootLines)
    return allLines


def find_author(lines, dummy):
    author, title = None, None

    for i, l in enumerate(lines):
        if author_regex.search(l):  # look for an author format match
            author = l
            break

    if author:
        if i >= 2:  # author is after the second line (where we expect the title)
            title = " ".join(lines[1:i])
        elif i == 1:  # author is the second line
            title = lines[2]
    else:
        title = lines[1]  # default to the title being the second line

    return title, author


def isbn_search(x):
    res = isbn_regex.search(x)
    if res:
        return res.group()
    else:
        return None


p5_root = (
    r"G:\DigiSchol\Digital Research and Curator Team\Projects & Proposals\00_Current Projects"
    r"\LibCrowds Convert-a-Card (Adi)\OCR\20230504 TKB Export P5 175 GT pp\1016992\P5_for_Transkribus"
)

if LOAD_XMLS:
    page_xml_loc = os.path.join(p5_root, "page")

    attempts = 0
    while attempts < 3:
        xmls = glob.glob(os.path.join(page_xml_loc, "*.xml"))
        if len(xmls) > 0:
            break
        else:
            attempts += 1
            continue
    else:
        raise IOError(f"Failed to connect to {page_xml_loc}")

    xmlroots = []

    print(f"\nGetting xml roots from {page_xml_loc}")
    for file in tqdm(xmls):
        fileName = os.fsdecode(file)
        attempts = 0
        while attempts < 3:
            try:
                tree = ET.parse(fileName)
                break
            except FileNotFoundError:
                attempts += 1
                continue
        else:
            raise FileNotFoundError(f"Failed to connect to: {fileName}")
        root = tree.getroot()
        xmlroots.append(root)

    cards = extractLinesForVol(xmlroots)
    cards_df_v0 = pd.DataFrame(
        data={
            "xml": [os.path.basename(x) for x in xmls],
            "lines": cards,
            "dummy": [None for x in cards]
        }
    )

    cards_df_v0["shelfmark"] = cards_df_v0["lines"].transform(lambda x: smark_regex.search(x[0]).group()).str.replace(" ", "")
    t_a = cards_df_v0.loc[:,('lines', 'dummy')].transform(lambda x: find_author(x[0], x[1]), axis=1).rename(columns={"lines":"title", "dummy":"author"})
    cards_df = cards_df_v0.drop(columns="dummy").join(t_a)
    cards_df["ISBN"] = cards_df["lines"].transform(lambda x:isbn_search("".join(x))).str.replace("ISBN ", "").str.strip()

    res = pickle.load(open("notebooks\\res.p", "rb"))
    cards_df['worldcat_result'] = res

    with open("notebooks\\cards_df.p", "wb") as f:
        pickle.dump(cards_df, f)

if LOAD_PICKLE:
    cards_df = pickle.load(open("notebooks\\cards_df.p", "rb"))
    # cards_df["xml"] = cards_df["xml"].str.decode("utf-8")

nulls = len(cards_df) - len(cards_df.dropna(subset="worldcat_result"))
errors = len(cards_df.query("worldcat_result == 'Error'"))
to_show = cards_df.query("worldcat_result != 'Error'").dropna(subset="worldcat_result")
st.markdown("# Worldcat results for searches for catalogue card title/author")
st.write(f"\nTotal of {len(cards_df)} cards")
st.write(f"Showing {len(to_show)} cards with Worldcat results, omitting {nulls} without results and {errors} with errors in result retrieval")
st.dataframe(to_show.loc[:,("title", "author", "shelfmark", "worldcat_result", "lines")])

option = st.selectbox(
    "Which result set do you want to choose between?",
    pd.Series(to_show.index, index=to_show.index, dtype=str) + " ti: " + to_show["title"] + " au: " + to_show["author"]
)
"Current selection: ", option
idx = int(option.split(" ")[0])
card_jpg_path = os.path.join(p5_root, to_show.loc[idx, "xml"][:-4] + ".jpg")

st.image(Image.open(card_jpg_path))

st.markdown("## Select from worldcat results")

c1, c2, c3 = st.columns(3)
res_to_pick = [0,1,2]

with c1:
    res = to_show.loc[idx, "worldcat_result"][res_to_pick[0]].get_fields()
    st.dataframe(pd.DataFrame(index=[int(x.tag) for x in res], data=[x.text() for x in res], columns=[res_to_pick[0]]))

with c2:
    res = to_show.loc[idx, "worldcat_result"][res_to_pick[1]].get_fields()
    st.dataframe(pd.DataFrame(index=[int(x.tag) for x in res], data=[x.text() for x in res], columns=[res_to_pick[1]]))

with c3:
    res = to_show.loc[idx, "worldcat_result"][res_to_pick[2]].get_fields()
    st.dataframe(pd.DataFrame(index=[int(x.tag) for x in res], data=[x.text() for x in res], columns=[res_to_pick[2]]))

good_res = st.radio(
    "Which is the correct Worldcat result?",
    (*res_to_pick, "None of the results are correct")
)

# res_dict, res = oclc.OCLC_orig_query("FENG JIAN ZHU YI DE SHENG CHAN FANG SHI", "ZHANG (Yu)")

# # print(result[0])
# print("hello")