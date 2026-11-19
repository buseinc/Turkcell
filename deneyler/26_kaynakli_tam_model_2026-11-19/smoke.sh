set -e
A="--sites 0 --ues 328 --duration 1.2 --sites-file inputs/sites_S0TA_42.csv --ue-file inputs/ues_LC_TA_701.csv --udp-jitter 1 --mixed-cqi 1 --measurement-ues 256 --pathloss rma --exponent 3 --beamwidth 65 --enb-power 49 --receiver-nf 9 --shadow-std 0 --dl-earfcn 1651 --ul-earfcn 19651 --indoor-loss 0 --downtilt 6 --vertical-pattern 1 --vertical-beamwidth 10 --link-shadow-std 8 --antenna-3gpp 1 --max-attenuation 25 --shadow-seed 42"
python3 simulation/run_baseline.py $A --name smoke_evm0 > logs_smoke_evm0.log 2>&1
python3 simulation/run_baseline.py $A --evm 0.08 --name smoke_evm8 --skip-build > logs_smoke_evm8.log 2>&1
echo done
