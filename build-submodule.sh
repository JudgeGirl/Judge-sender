#!/bin/sh

rm -rf dependency/*
cd submodules/Judge-common
poetry build
cd ../..
cp submodules/Judge-common/dist/judge_common* dependency
