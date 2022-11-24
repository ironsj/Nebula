#!/bin/bash

error_handler() {
  echo "******* FAILED *******" 1>&2
  exit 1
}

trap error_handler ERR

apt install -y curl

curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash

apt-get install -y nodejs

apt install -y python python3-pip

apt update

apt install -y openjdk-8-jdk

apt install -y ant

apt-get install ca-certificates-java

apt clean

update-ca-certificates -f

pip3 install --upgrade pip

pip3 install -e ./Nebula-Pipeline

python3 -m nltk.downloader stopwords

npm install -g npm@9.1.2

npm install -g nodemon@^2.0.15

npm install

pip3 install -U scikit-learn