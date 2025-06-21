import streamlit as st
import requests
from datetime import datetime, timezone
from streamlit_autorefresh import st_autorefresh

st_autorefresh(interval=30 * 1000) # refresh every 30 seconds

# api source: https://data.gov.hk/en-data/dataset/hk-td-tis_21-etakmb

@st.cache_data(show_spinner="Downloading data ...")
def load_data(url):
    response = requests.get(url)
    if response.status_code == 200:
        rs = response.json()["data"]
        return rs
    else:
        return []

def load_fresh_data(url):
    response = requests.get(url)
    if response.status_code == 200:
        rs = response.json()["data"]
        return rs
    else:
        return []
    
def show_eta(t):
    secs = int(t)
    mm = (secs//60)+1
    if mm == 1:
        return st.metric("Estimated Time", f"{mm:d} min")
    return st.metric("Estimated Time", f"{mm:d} mins")

lang_map = {
    "en": "En",
    "tc": "繁",
    "sc": "简",
}

lang = st.segmented_control(
    "Language",
    lang_map.keys(),
    format_func=lambda option: lang_map[option],
    selection_mode="single",default = "en", label_visibility="hidden"
)

if not lang:
    lang="en" # if no default value or removed the selection, set "en"

url = "https://data.etabus.gov.hk/v1/transport/kmb/route/"
routes_data = load_data(url)
routes = sorted(list(set([r["route"] for r in routes_data])))

bus_list = st.multiselect(
    "Search Bus Route",
    routes
)

for bus in bus_list:
    with st.expander(f"{bus}"):
        inbound = st.toggle("Reverse Route",label_visibility="visible", key=bus+" bound")
        
        if inbound:
            url1 = f"https://data.etabus.gov.hk/v1/transport/kmb/route/{bus}/inbound/1"
            url2 = f"https://data.etabus.gov.hk/v1/transport/kmb/route-stop/{bus}/inbound/1"
            direction = "I"
        else:
            url1 = f"https://data.etabus.gov.hk/v1/transport/kmb/route/{bus}/outbound/1"
            url2 = f"https://data.etabus.gov.hk/v1/transport/kmb/route-stop/{bus}/outbound/1"
            direction = "O"
            
        route = load_data(url1)
        
        if route:
            st.header(f"{bus}")
            st.subheader(f"{route[f"orig_{lang}"]} → {route[f"dest_{lang}"]}".title())
            
            stops = load_data(url2)
            stop_ids = [ s["stop"] for s in stops]

            stops_info = {}
            for sid in stop_ids:
                url3 = f"https://data.etabus.gov.hk/v1/transport/kmb/stop/{sid}"
                r_stop = load_data(url3)
                stops_info[sid] = r_stop[f"name_{lang}"]
            
            # select the stop
            bus_stop_id = st.select_slider(
                "Select a stop",
                options=stop_ids, key = f"{bus} stop slider",
                format_func = lambda x: " ".join(stops_info[x].title().split()[:-1]),
            )
            
            url4 = f"https://data.etabus.gov.hk/v1/transport/kmb/eta/{bus_stop_id}/{bus}/1"
            ETAs = load_fresh_data(url4)
            ETAs = [ e for e in ETAs if e["dir"] == direction]
            times = [ e["eta"] for e in ETAs]
            num = len(times)
            columns = st.columns(num)
            for idx, col in enumerate(columns):
                
                with col: 
                    target_time = times[idx]
                    if target_time:
                        diff = datetime.strptime(target_time, "%Y-%m-%dT%H:%M:%S%z") - datetime.now(timezone.utc)
                        show_eta(int(diff.total_seconds()))
                    else:
                        st.error(ETAs[idx][f"rmk_{lang}"])

        else:
            st.subheader(f"Cannot find this route {bus} ({direction})")
            

