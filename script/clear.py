from tqdm import tqdm

from model.tax import Tax

if __name__ == "__main__":
    with Tax.batch_write() as batch:
        for item in tqdm(Tax.scan(Tax.address != "test")):
            batch.delete(item)
