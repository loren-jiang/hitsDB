# hitsDB
Database written using mostly Python, Django, PostgreSQL to manage data in HITS pipeline.

![gui](https://d27i862zg3bohz.cloudfront.net/lj-media/hitsDB_imageGUI.png "gui")

## Overview
Basic site live: [demo](https://hitsdb-demo.herokuapp.com/)

This Django web app was created to streamline the data collection and organization for a research pipeline called High Isomorphism Throughput Screening (HITS). The main features of this app are:
- user authentication and account recovery
- PostgreSQL database to store information necessary to keep track of experimental progress
- an image user interface for quickly setting data markers
- integration with AWS s3 for media file storage
