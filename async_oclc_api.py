import asyncio
from datetime import datetime
import logging
import os
import pickle
import time

from src.data.oclc_api import cac_search_kwargs, music_search_kwargs, process_queue

import bookops_worldcat as bw
from dotenv import load_dotenv
import pandas as pd
from tqdm import tqdm

load_dotenv()
client_id = os.environ["CLIENT_ID"]
client_secret = os.environ["CLIENT_SECRET"]


# cards_df = pickle.load(open("data\\processed\\401_cards_no_oclc.p", "rb"))
# cards_df["brief_bibs"] = None
# cards_df["worldcat_matches"] = None

# complete_music_df = pd.read_csv("data\\processed\\music_records.csv", index_col=0, dtype={"260": str})
# music_df = complete_music_df.sample(n=10000, weights="weights", axis=0, random_state=1234)
# music_df = music_df.where(~music_df.isna(), other=None)
# music_df["brief_bibs"] = None
# music_df["worldcat_matches"] = None

music_df = pickle.load(open("data\\processed\\10k_music_records.p", "rb"))

token = bw.WorldcatAccessToken(
    key=client_id,
    secret=client_secret,
    scopes="WorldCatMetadataAPI",
    agent="ConvertACard/1.0"
)

# session = bw.MetadataSession(authorization=token)
# res = session.brief_bibs_search('ti:"FENG LING DU" and au:"DUANMU (Hongliang)"', **search_kwargs)


async def main(records_df, out_path):

    brief_bibs = records_df["brief_bibs"].to_dict()
    full_bibs = records_df["worldcat_matches"].to_dict()
    full_bibs = {k: [] for k in full_bibs}

    async with bw.AsyncMetadataSession(authorization=token, headers={"User-Agent": "Convert-a-Card/1.0"}) as session:

        queue = asyncio.Queue()
        subset = records_df.iloc[:]
        for row in subset.iterrows():
            idx = row[0]

            # title, author, isbn = row[1].loc[["title", "author", "isbn"]]
            # await queue.put((idx, title, author, isbn))

            # title, author, year = row[1].loc[["245", "100", "260"]]
            # await queue.put((idx, title, author, year))
            if row[1]["brief_bibs"]["numberOfRecords"] > 0:
                for rec in row[1]["brief_bibs"]["briefRecords"]:
                    if rec["catalogingInfo"]["catalogingAgency"] != "UKMGB":
                        await queue.put((idx, rec["oclcNumber"]))

        print("Creating workers")
        print("brief bib search API call progress:")
        tracker = tqdm(total=queue.qsize())

        tasks = []
        n_workers = 50  # 25 gave no errors for 5000 records

        for i in range(n_workers):  # create workers
            task = asyncio.create_task(
                process_queue(
                    queue=queue,
                    name=f'worker-{i}',
                    session=session,
                    search_kwargs=music_search_kwargs,
                    brief_bibs_out=brief_bibs,
                    full_bibs_out=full_bibs,
                    tracker=tracker
                )
            )

            tasks.append(task)

        global run_id
        t0 = time.perf_counter()
        logging.info(f"{run_id} OCLC query queue joined")

        await queue.join()

        t1 = time.perf_counter()
        logging.info(f"{run_id} OCLC query queue complete - elapsed: {t1 - t0}")

        for task in tasks:
            task.cancel()

        # await asyncio.gather(*tasks, return_exceptions=True)

        # records_df["brief_bibs"] = brief_bibs
        records_df["worldcat_matches"] = full_bibs
        pickle.dump(records_df, open(out_path, "wb"))


if __name__ == "__main__":
    print("\nInitialising loggers")
    today = datetime.now().strftime("%y%m%d")
    complete_log = f"logs\\{today}_tag_removal_debug_async.log"
    progress_log = f"logs\\{today}_tag_removal_progress_async.log"
    error_log = f"logs\\{today}_tag_removal_error_async.log"

    logging.basicConfig(filename=complete_log,
                        format='%(asctime)s %(name)-12s %(levelname)-8s %(message)s',
                        datefmt='%m-%d %H:%M',
                        encoding='utf-8',
                        level=logging.DEBUG)

    # All logging statements go to complete_log, only logging.info statements go to progress_log
    progress = logging.FileHandler(filename=progress_log)
    progress.setLevel(logging.INFO)
    prog_formatter = logging.Formatter('%(asctime)s %(name)-12s %(levelname)-8s %(message)s', datefmt='%m-%d %H:%M')
    progress.setFormatter(prog_formatter)
    logging.getLogger("").addHandler(progress)

    error = logging.FileHandler(filename=error_log)
    error.setLevel(logging.ERROR)
    err_formatter = logging.Formatter('%(asctime)s %(name)-12s %(levelname)-8s %(message)s', datefmt='%m-%d %H:%M')
    error.setFormatter(err_formatter)
    logging.getLogger("").addHandler(error)

    run_id = '0001'

    print("Running async loop\n")
    t_init = time.perf_counter()
    logging.info(f"{run_id} async begin = {t_init}")

    asyncio.run(main(music_df, "data\\processed\\10k_music_records_debug.p"))

    t_final = time.perf_counter()
    logging.info(f"{run_id} async elapsed = {t_final - t_init}")
