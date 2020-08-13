set -e

yesterday=$(date -d "yesterday 13:00" +%Y-%m-%d)
# yesterday="2020-07-25"
wget  -O ~/efs-mnt/raw.tar.gz "https://ai2-semanticscholar-cord-19.s3-us-west-2.amazonaws.com/historical_releases/cord-19_${yesterday}.tar.gz"
tar -zxvf ~/efs-mnt/raw.tar.gz -C ~/efs-mnt/

rm ~/efs-mnt/raw.tar.gz
rm -rf ~/efs-mnt/latest_new # remove file and ignore if it doesn't exist
mv ~/efs-mnt/${yesterday} ~/efs-mnt/latest_new
tar -zxvf ~/efs-mnt/latest_new/cord_19_embeddings.tar.gz -C ~/efs-mnt/latest_new/
mv ~/efs-mnt/latest_new/cord_19_embeddings_${yesterday}.csv ~/efs-mnt/latest_new/cord_19_embeddings.csv
rm ~/efs-mnt/latest_new/cord_19_embeddings.tar.gz
tar -zxvf ~/efs-mnt/latest_new/document_parses.tar.gz -C ~/efs-mnt/latest_new/
rm ~/efs-mnt/latest_new/document_parses.tar.gz


# prepare files for parsing
cp -r ~/efs-mnt/static_files/scibert_scivocab_uncased ~/efs-mnt/latest_new
cp ~/efs-mnt/static_files/cord_uid_to_summaries_short.pkl ~/efs-mnt/latest_new/
cp ~/efs-mnt/static_files/keywords_intermediate.pkl ~/efs-mnt/latest_new/ 
cp ~/efs-mnt/static_files/cord_uid_to_keywords.pkl ~/efs-mnt/latest_new/ 
/home/ubuntu/anaconda3/envs/w210_et/bin/python ~/capstone_corona_search/scripts/parse_covid_data.py

# copy newly created files to root
cp ~/efs-mnt/latest_new/cord_uid_to_summaries_short.pkl ~/efs-mnt/static_files/
cp ~/efs-mnt/latest_new/phraser.pkl ~/efs-mnt/static_files/
cp ~/efs-mnt/latest_new/keywords_intermediate.pkl ~/efs-mnt/static_files/
cp ~/efs-mnt/latest_new/cord_uid_to_keywords.pkl ~/efs-mnt/static_files/

# move new version on top of old version
rm -rf ~/efs-mnt/latest_bak
mv ~/efs-mnt/latest ~/efs-mnt/latest_bak
rm -rf ~/efs-mnt/latest
cp -r ~/efs-mnt/latest_new ~/efs-mnt/latest
