#!/bin/sh

# Number of votes to create
VOTES_A=2000
VOTES_B=1000
CONCURRENCY=50
URL="http://vote/"
CONTENT_TYPE="application/x-www-form-urlencoded"

# Create votes for option A
ab -n $((VOTES_A / 2)) -c $CONCURRENCY -p posta -T "$CONTENT_TYPE" "$URL"
ab -n $((VOTES_A / 2)) -c $CONCURRENCY -p posta -T "$CONTENT_TYPE" "$URL"

# Create votes for option B
ab -n $VOTES_B -c $CONCURRENCY -p postb -T "$CONTENT_TYPE" "$URL"
