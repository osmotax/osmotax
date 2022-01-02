# osmotax
`osmotax` is a tax tracker that checks how many OSMO-LP rewards you have received every day.

## scripts
1. Create `meatadata` with epoch, timestamp and osmo price recorded in one row.
    ```shell
    $ python -m script.create_metadata \
        --output epoch_height_price.csv \
        --start_epoch 1 \
        --end_epoch 150
   ```
   The created metadata is as follows:
   ```text
    # epoch_height_price.csv
    epoch,height,time,price
    ...
    6,79332,2021-06-24T17:01:02.632475507Z,7.1755643477
    7,92895,2021-06-25T17:01:14.14128212Z,6.6011321864
    8,106555,2021-06-26T17:01:23.669020671Z,5.5413647041
    9,120105,2021-06-27T17:01:30.931417539Z,5.3491279762
    ...
   ```

2. Download `block_result` corresponding to block height in json format.
   ```shell
    $ python -m script.download \
       --metadata epoch_height_price.csv \
       --start_epoch 1 \
       --end_epoch 150
   ```
3. Create DB with AWS dynamodb
   ```shell
    $ aws configure
    $ python -m script.create_db \
        --metadata epoch_height_price.csv
   ```
4. (Optioanl) Check the actual osmo distribution amount.
   ```shell
    $ python -m script.check \
        --metadata epoch_height_price.csv \
        --num 5 \ # get only 5 days from `last_date`
        --last_date 2021-12-13
        --
   ```
   
## Run flask application
Before running flask script, create `config.py` in `app/` folder and set RECAPTCHA related config as below
```python
RECAPTCHA_SITE_KEY = ""
RECAPTCHA_SECRET_KEY = ""
```
Then, run flask application script
```shell
sudo apt install authbind

# Configure access to port 80
sudo touch /etc/authbind/byport/80
sudo chmod 777 /etc/authbind/byport/80
authbind --deep python -m app.app --port 80
```