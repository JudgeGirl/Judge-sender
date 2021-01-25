#!/bin/bash

cp /home/judgesister/Judge-common/dist/*.whl ./dependency/
poetry add ./dependency/*.whl
