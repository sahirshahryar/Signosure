# Signosure Architecture and API

As an end-to-end data collection, annotation, and processing server for sign
language datasets, Signosure has the following components:

* User management (researchers, collectors, and annotators)
* Dataset management
* A data collection service (`collection/`)
* A data processing service (`processing/`)
* A data annotation interface (`annotation/`)
* Visualization tools (`visualization/`)
* A user interface which combines all of these (`interface/`)

This document lists out the APIs for each of these components.
