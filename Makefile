#####################################################################
# Makefile for Premier League Knowledge Base Data Pipeline
#
# This Makefile orchestrates the crawling and transformation of raw
# Premier League data into structured knowledge base components. The
# pipeline consists of several steps:
#   1. crawl-players       – Crawl player data for a range of seasons.
#   2. build-players       – Aggregate player records and relationships.
#   3. build-clubs         – Construct club records and relationships.
#   4. build-player-stats  – Fetch player statistics per season.
#   5. build-seasons       – Derive season records from stats.
#   6. build-positions     – Extract position entities from players.
#   7. build-nationalities – Extract nationality entities from players.
#   8. crawl-all           – Run the entire pipeline end-to-end.
#
# Variables can be overridden on the command line, e.g.:
#   make crawl-players START_SEASON=2010 END_SEASON=2020
#
#####################################################################

PYTHON          ?= python3
SCRIPTS_DIR     ?= scripts
RAW_DATA_DIR    ?= raw_data

RDF_SCRIPTS_DIR   ?= rdf_scripts
RDF_OUTPUT_DIR    ?= rdf_output

# Default seasons (inclusive) used by crawl-all if not provided
START_SEASON    ?= 2020
END_SEASON      ?= 2024

# Competition identifier for Premier League
COMPETITION_ID  ?= 8

.PHONY: setup crawl-players build-players build-clubs build-player-stats build-seasons build-positions build-nationalities crawl-all

# Ensure the raw data directory exists
setup:
	mkdir -p $(RAW_DATA_DIR)
	mkdir -p $(RDF_OUTPUT_DIR)

# Step 1: Crawl players for the specified season range
crawl-players: setup
	$(PYTHON) $(SCRIPTS_DIR)/crawl_players.py \
		--competition-id $(COMPETITION_ID) \
		--start-season $(START_SEASON) \
		--end-season $(END_SEASON) \
		--output $(RAW_DATA_DIR)/players_by_season.json

# Step 2: Build aggregated player records and relationships
build-players: setup
	$(PYTHON) $(SCRIPTS_DIR)/build_players.py \
		--input $(RAW_DATA_DIR)/players_by_season.json \
		--output $(RAW_DATA_DIR)/players.json \
		--competition-id $(COMPETITION_ID)

# Step 3: Build club records
build-clubs: setup
	$(PYTHON) $(SCRIPTS_DIR)/build_clubs.py \
		--input $(RAW_DATA_DIR)/players_by_season.json \
		--output $(RAW_DATA_DIR)/clubs.json

# Step 4a: Build player season statistics
build-player-stats: setup
	$(PYTHON) $(SCRIPTS_DIR)/build_player_stats.py \
		--input $(RAW_DATA_DIR)/players_by_season.json \
		--output $(RAW_DATA_DIR)/player_season_stats.json \
		--competition $(COMPETITION_ID)

# Step 5: Build season records from player statistics
build-seasons: setup
	$(PYTHON) $(SCRIPTS_DIR)/build_seasons.py \
		--input $(RAW_DATA_DIR)/player_season_stats.json \
		--output $(RAW_DATA_DIR)/seasons.json

# Step 6: Build positions from aggregated players
build-positions: setup
	$(PYTHON) $(SCRIPTS_DIR)/build_positions.py \
		--input $(RAW_DATA_DIR)/players.json \
		--output $(RAW_DATA_DIR)/positions.json

# Step 7: Build nationalities from aggregated players
build-nationalities: setup
	$(PYTHON) $(SCRIPTS_DIR)/build_nationalities.py \
		--input $(RAW_DATA_DIR)/players.json \
		--output $(RAW_DATA_DIR)/nationalities.json

aggregate-totals-to-players:setup
	$(PYTHON) $(SCRIPTS_DIR)/aggregate_totals_to_players.py \
		--stats $(RAW_DATA_DIR)/player_season_stats.json \
		--players $(RAW_DATA_DIR)/players.json \
		--output $(RAW_DATA_DIR)/players.json

# Step 8: Run the entire pipeline
crawl-all: crawl-players build-players build-clubs build-player-stats build-seasons build-positions build-nationalities argregate-totals-to-players
	@echo "Data pipeline completed. Files are stored in $(RAW_DATA_DIR)."


# Convert raw data to RDF format
rdf-players: setup
	$(PYTHON) $(RDF_SCRIPTS_DIR)/player_to_rdf.py \
		--input $(RAW_DATA_DIR)/players.json \
		--output $(RDF_OUTPUT_DIR)/players.ttl

rdf-clubs: setup
	$(PYTHON) $(RDF_SCRIPTS_DIR)/club_to_rdf.py \
		--input $(RAW_DATA_DIR)/clubs.json \
		--output $(RDF_OUTPUT_DIR)/clubs.ttl

rdf-season:
	$(PYTHON) $(RDF_SCRIPTS_DIR)/season_to_rdf.py \
		--input $(RAW_DATA_DIR)/seasons.json \
		--output $(RDF_OUTPUT_DIR)/seasons.ttl

rdf-player-stats:
	$(PYTHON) $(RDF_SCRIPTS_DIR)/player_stats_to_rdf.py \
		--input $(RAW_DATA_DIR)/player_season_stats.json \
		--output $(RDF_OUTPUT_DIR)/player_stats.ttl

rdf-position:
	$(PYTHON) $(RDF_SCRIPTS_DIR)/position_to_rdf.py \
		--input $(RAW_DATA_DIR)/positions.json \
		--output $(RDF_OUTPUT_DIR)/positions.ttl

rdf-nationalities:
	$(PYTHON) $(RDF_SCRIPTS_DIR)/nationality_to_rdf.py \
	--input $(RAW_DATA_DIR)/nationalities.json \
	--output $(RDF_OUTPUT_DIR)/nationalities.ttl

rdf-all: rdf-players rdf-clubs rdf-season rdf-player-stats rdf-position rdf-nationalities
	@echo "RDF conversion completed. Files are stored in $(RDF_OUTPUT_DIR)."


graphdb-run:
	docker run -d --name graphdb \
	  -p 7200:7200 \
	  -v $(shell pwd)/graphdb-data:/opt/graphdb/home \
	  ontotext/graphdb:10.8.3

graphdb-clean:
	docker stop graphdb || true
	docker rm graphdb || true
	rm -rf graphdb-data

graphdb-restart: graphdb-clean graphdb-run
	@echo "GraphDB restarted."


run-sparql-batch:
	$(PYTHON) sparql_docs/run_sparql_batch.py \
		--file sparql_docs/SPARQL_Query_Examples.rq \
		--endpoint http://localhost:7200/repositories/premier-league