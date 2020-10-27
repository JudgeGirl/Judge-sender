#!/bin/bash

cp ../Judge-common/dist/*.whl dependency
poetry add ./dependency/*.whl
