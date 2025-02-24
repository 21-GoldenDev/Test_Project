# Description: Initialize Riva services
bash riva_quickstart_v2.18.0/config.sh
bash riva_quickstart_v2.18.0/init.sh
bash riva_quickstart_v2.18.0/riva_start.sh

# Check if the Riva services are running
docker ps

# Create a new conda environment and install the required packages
git clone https://github.com/nvidia-riva/python-clients.git
cd python-clients
conda create -n riva python=3.9
conda activate riva
git submodule init
git submodule update --remote --recursive
pip install -r requirements.txt
python3 setup.py bdist_wheel
pip install --force-reinstall dist/*.whl
pip install nvidia-riva-client
conda install -c anaconda pyaudio
pip install -U scikit-learn
pip install -U transformers
cd ..
python3 transcribe_mic.py
