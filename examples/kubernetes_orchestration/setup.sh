#!/usr/bin/env bash

set -Eeo pipefail

pre_run () {
  zenml integration install sklearn facets kubernetes
}

pre_run_forced () {
  zenml integration install sklearn facets kubernetes -y
}
