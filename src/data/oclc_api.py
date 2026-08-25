from asyncio import Queue
import io
import logging
import time
from typing import Dict, List, Optional, Union

from bookops_worldcat import MetadataSession, AsyncMetadataSession
from bookops_worldcat.errors import WorldcatRequestError
from pymarc import marcxml, Record
from tqdm import tqdm

cac_search_kwargs = {
    "inCatalogLanguage": None,
    "limit": 50,
    "orderBy": "bestMatch",
    "itemSubType": "artchap-artcl, book-mic, book-thsis, book-printbook, jrnl-print"
}

music_search_kwargs = {
    "inCatalogLanguage": None,
    "limit": 50,
    "orderBy": "bestMatch",
    "itemSubType": "msscr-mss, msscr-"
}


def search_brief_bib(
    ti: Optional[str] = None,
    au: Optional[str] = None,
    isbn: Optional[Union[str, int]] = None,
    session: MetadataSession = None,
    search_kwargs: Optional[Dict[str, Union[None, int, str]]] = {}
) -> Dict[str, str]:
    """
    search_brief_bib applicable to df
    Known issue with specifying offset/limit
    So specify acceptable itemSubTypes and hope correct result is in first 50 records
    """

    res = None

    if isbn:
        query = f'bn:{isbn}'
        res = session.brief_bibs_search(q=query, **search_kwargs)

    if not res or res.json()["numberOfRecords"] == 0:
        query = f'ti:"{ti}" and au:"{au}"'
        res = session.brief_bibs_search(q=query, **search_kwargs)

    return res.json()


def get_full_bib(
    brief_bibs: Dict[str, Union[int, Dict[str, str]]],
    session: MetadataSession
) -> Union[None, List[Record]]:
    if brief_bibs["numberOfRecords"] == 0:
        return None
    else:
        recs = brief_bibs["briefRecords"]
        oclc_nums = [x["oclcNumber"] for x in recs]
        if len(set(oclc_nums)) != len(oclc_nums):
            raise ValueError("Non unique OCLC numbers returned by brief bibs search")
        matched_xml = [session.bib_get(rec["oclcNumber"]).text for rec in recs]
        matched_records = [marcxml.parse_xml_to_array(io.StringIO(x))[0] for x in matched_xml]
        return matched_records


async def process_queue(
    queue: Queue,
    name: Optional[str] = None,
    session: AsyncMetadataSession = None,
    search_kwargs: Optional[Dict[str, Union[None, int, str]]] = {},
    brief_bibs_out: Dict[int, Union[None, str, Dict[str, str]]] = {},
    full_bibs_out: Dict[int, List[Union[Record, str]]] = {},
    tracker: tqdm = None
):
    while True:
        work_item = await queue.get()

        if len(work_item) == 4:  # idx, ti, au, year from music_records_df
            t0 = time.perf_counter()
            logging.debug(f"{name} api brief call start {t0}")

            idx, ti, au, year = work_item
            try:
                brief_bibs = await async_search_brief_bib_music(ti=ti, au=au, year=year, session=session, search_kwargs=search_kwargs)
                brief_bibs_out[idx] = brief_bibs

                # if brief_bibs["numberOfRecords"] > 0:
                #     await asyncio.gather(*[queue.put((idx, res["oclcNumber"])) for res in brief_bibs["briefRecords"]])

                tracker.update(n=1)
                t1 = time.perf_counter()
                logging.debug(f"{name} api brief call finished. Elapsed: {t1 - t0}")
                queue.task_done()
            except WorldcatRequestError as e:
                brief_bibs_out[idx] = f"{e}"
                queue.task_done()

        elif len(work_item) == 400:  # idx, ti, au, isbn from cards_df
            t0 = time.perf_counter()
            logging.debug(f"{name} api brief call start {t0}")

            idx, ti, au, isbn = work_item
            try:
                brief_bibs = await async_search_brief_bib_cac(ti=ti, au=au, isbn=isbn, session=session, search_kwargs=search_kwargs)
                brief_bibs_out[idx] = brief_bibs

                # if brief_bibs["numberOfRecords"] > 0:
                #     await asyncio.gather(*[queue.put((idx, res["oclcNumber"])) for res in brief_bibs["briefRecords"]])

                tracker.update(n=1)
                t1 = time.perf_counter()
                logging.debug(f"{name} api brief call finished. Elapsed: {t1 - t0}")
                queue.task_done()
            except WorldcatRequestError as e:
                brief_bibs_out[idx] = f"{e}"
                queue.task_done()

        elif len(work_item) == 2:  # idx, oclc number from a brief bib

            t0 = time.perf_counter()
            logging.debug(f"{name} api full call start {t0}")

            idx, oclc_num = work_item
            try:
                xml = await session.bib_get(oclc_num)
                record = marcxml.parse_xml_to_array(io.StringIO(xml.text))[0]
                full_bibs_out[idx].append(record)

                t1 = time.perf_counter()
                logging.debug(f"{name} api full call finished. Elapsed: {t1 - t0}")
                queue.task_done()
                tracker.update(n=1)
            except WorldcatRequestError as e:
                full_bibs_out[idx].append(f"{e}")
                queue.task_done()
                tracker.update(n=1)


async def async_search_brief_bib_cac(
    ti: Optional[str],
    au: Optional[str],
    isbn: Optional[int],
    session: AsyncMetadataSession = None,
    search_kwargs: Optional[Dict[str, Union[None, int, str]]] = {}
) -> Dict[str, str]:
    """
    Async version of search_brief_bib
    Known issue with specifying offset/limit
    So specify acceptable itemSubTypes and hope correct result is in first 50 records
    """
    res = None

    if isbn:
        query = f'bn:{isbn}'
        res = await session.brief_bibs_search(q=query, **search_kwargs)

    if not res or res.json()["numberOfRecords"] == 0:
        query = f'ti:"{ti}" and au:"{au}"'
        res = await session.brief_bibs_search(q=query, **search_kwargs)

    return res.json()


async def async_search_brief_bib_music(
    ti: Optional[str],
    au: Optional[str],
    year: Optional[int],
    session: AsyncMetadataSession = None,
    search_kwargs: Optional[Dict[str, Union[None, int, str]]] = {}
) -> Dict[str, str]:
    """
    Async version of search_brief_bib
    Known issue with specifying offset/limit
    So specify acceptable itemSubTypes and hope correct result is in first 50 records
    """
    query = f'ti:"{ti}" AND au:"{au}" AND yr:{year}'
    res = await session.brief_bibs_search(q=query, **search_kwargs)

    return res.json()
