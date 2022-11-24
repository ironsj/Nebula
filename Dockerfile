FROM ubuntu:20.04
RUN mkdir /www
WORKDIR /www
RUN apt-get update

# Timezone added for some Python Dependencies 
ENV TZ=America/Detroit
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

# Install node v18.x
RUN apt-get install -y curl && \
        curl -sL https://deb.nodesource.com/setup_18.x | bash - && \
        apt-get install -y nodejs

# Install pip and necessary Python packages
RUN apt-get install -y python python3-pip

# Fix certificate issues, found as of 
# https://bugs.launchpad.net/ubuntu/+source/ca-certificates-java/+bug/983302
RUN apt-get update && \
        apt-get install -y openjdk-8-jdk && \
	apt-get install -y ant && \
        apt-get install ca-certificates-java && \
	apt-get clean && \
	update-ca-certificates -f;

# Setup JAVA_HOME, this is useful for docker commandline
ENV JAVA_HOME /usr/lib/jvm/java-8-openjdk-amd64/
RUN export JAVA_HOME

RUN pip3 install --upgrade pip

COPY . /www

RUN pip3 install -e ./Nebula-Pipeline
#RUN pip install numpy scipy cython zerorpc tweepy nltk elasticsearch
RUN python3 -m nltk.downloader stopwords
# Helps ensure all custom modules can be found
RUN export PYTHONPATH="${PYTHONPATH}:./Nebula-Pipeline"

# Install Nathan Wycoff's version of sklearn
COPY ./lib/ /opt/lib

RUN npm install -g npm@9.1.2
RUN npm install -g nodemon@^2.0.15
RUN npm install

RUN pip3 install -U scikit-learn

EXPOSE 4040

# Attempt to run npm withing a tmux sesssion
# Docker only seems to care about whatever command it's being launched with,
# meaning once the associated process ends, the Docker container stops running
# My hope was to make Docker "care" about a tmux session as opposed to npm,
# which would let you go in and restart npm as desired, but I couldn't quite
# get this working...
#CMD ["sh", "-c",  "tmux new-session -d -s nebula_session1 && tmux send-keys -t nebula_session1 'npm start' ENTER"]

CMD ["nodemon", "-L", "start"]
