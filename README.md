# About

Author: Delvin So
Last Updated: 2025-12-30

This repository contains the ELA Seasonality Dashboard, written in Python and using Streamlit as a dashboarding framework.

Data is fetched through [ELA's Data API](https://github.com/IISD-ELA/ela-api). Additional documentation pertaining to the endpoints will be added later. 

## Directory Structure

The following is the directory structure:

```
.
├── README.md
├── dashboard.py     # contains the core components, such as the tabs and layout of the plots, and data wrangling functions
├── get_data.py      # contains functions for fetching data from the ELA API
├── iisd_colours.py  # contains colours for IISD branding
├── plot.py          # contains functions for creating the various plots used in the dashboard
└── static/          # assets such as css, logo and fonts used in the dashboard
```

# Development/Local Instance

To run the dashboard locally, first install the requirements in your environment (it is recommended to use a venv or conda environment).

This can be done by running the following commands in the directory where you cloned this repository:

```
python -m venv .venv
source .venv/bin/activate
```

Next, run the following:

`pip install -r requirements.txt`

Then, to launch the dashboard in development mode:

`streamlit run dashboard.py`

You should see something like the following; to open the dashboard click on the URL:

```
  You can now view your Streamlit app in your browser.

  Local URL: http://localhost:8501
  Network URL: http://172.19.213.59:8501
```

## Deployment

Deployment should be done via [Streamlit Community Cloud](https://share.streamlit.io/) as a public app and is straightforward, all you need to do is provide the URL of this repo. The GitHub account `iisd-ela-data` is used to manage the app. To obtain access to the account, please contact Chris Hay (chay@iisd-ela.org).


## Future Work

- [ ] Change font of plotly figures to also use proxima
