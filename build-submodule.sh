#!/bin/sh

rm -rf dependency/*
cd common
poetry build
cd ../
cp common/dist/judge_common* dependency
