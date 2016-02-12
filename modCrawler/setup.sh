#!/usr/bin/env bash
# Consider running modTracker within a virtual env or container if you don't like to install all these new packages.
sudo apt-get update
sudo apt-get --yes --force-yes install python python2.7-dev python-pyasn1 python-setuptools python-pip python-dev libxml2-dev libxslt1-dev libffi-dev git screen libxss-dev xvfb firefox flashplugin-installer build-essential strace nano libssl-dev zlib1g-dev libjpeg8-dev

sudo easy_install pip
sudo pip install -r etc/requirements.txt

mkdir bins
mkdir jobs
mkdir tmp
cd etc
wget https://s3.amazonaws.com/alexa-static/top-1m.csv.zip
unzip top-1m.csv.zip
rm top-1m.csv.zip
cd ../bins

# Don't like downloading a binary? Use the provided patch to build your own Firefox. 
tar_ball="firefox-44.0.1.en-US.linux-x86_64.tar.bz2"
wget "https://securehomes.esat.kuleuven.be/~gacar/$tar_ball"
echo "1fd471fb882356a953d23dee5f0033332b99caae3fb4fb45daf4ef707142f9f9 $tar_ball" | sha256sum -c -
# Make sure the hash matches.

tar xvf firefox-44.0.1.en-US.linux-x86_64.tar.bz2
mv firefox ff-mod
# timeout 1 mitmdump  # this will create the certs in ~/.mitmproxy

echo "Setting up ptrace permissions, you may need to manually edit ptrace config if you get an error in the next step"
sudo echo 0 |sudo tee /proc/sys/kernel/yama/ptrace_scope
# if the above command fails
# Change the 1 in /proc/sys/kernel/yama/ptrace_scope to 0
echo "Setting ptrace to 0 (more permissive) has serious security implications."
echo "See, https://wiki.ubuntu.com/SecurityTeam/Roadmap/KernelHardening#ptrace_Protection"
echo "Setup is finished."
