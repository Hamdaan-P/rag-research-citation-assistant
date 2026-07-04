# app/config.py

# Maximum distance a retrieved chunk's best match may have to be considered
# relevant (smaller distance = more similar). This value must stay in sync
# across generate.py and main.py, which is exactly why it now lives here.
RELEVANCE_THRESHOLD = 1.0
