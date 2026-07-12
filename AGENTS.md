# Signosure agent guide
Signosure is a comprehensive data collection tool for sign language. This document is provided for LLMs that write code within this repository.

## Background
When creating ML/AI tools for the Deaf community, insufficient or low-quality data is a major concern. Most available data is not sufficiently annotated to be useful for machine learning, and different regions of the world each have different sign languages, each of which is a full, rich language in its own right, with distinct ancestries from their corresponding spoken languages. American Sign Language and British Sign Language, for example, have vastly different signs for the same concepts. There can also be significant regional variation between sign languages, such as between the Northeastern U.S. and the Southern U.S.

In order to efficiently collect the data necessary to build useful sign language models, we have built a patchwork of disparate tools that each solve one of the many problems building sign language datasets. These problems include:

- **Collecting labeled sign language data**. It is relatively easy to find videos of Deaf people signing, but much more difficult to find *labeled* data that can be used for effective training. To alleviate this, we ask users to 
record themselves signing a specific prompt, and create videos which only contain that prompt.
- **Annotating the collected data**. Because of regional variations within a language, some contributors may provide different signs for the same prompt. (This can be useful data to keep for the long term to capture regional variations, but in the short term, it can substantially reduce the accuracy of a recognizer model.) Sometimes, contributors may accidentally record with someone else in the background, in which case the video needs to be discarded to comply with universities' Institutional Review Board policies on the collection of personal information. In other cases, contributors may tap the record button too late, or stop recording too early, to capture the full motion of the sign. (To help prevent the last problem, the app we use for data collection records continuously, and we keep timestamps for when the user starts/stops recording.) In all of these cases, having humans review the collected data can massively improve the quality of the dataset, which is essential when the necessary data is so hard to come by.
- **Processing the collected data**. To make the collected videos easier for standard machine learning architectures to work with, we usually extract features from the video with pose detection models, such as MediaPipe. These tools dramatically reduce the feature space, reducing a computer vision task to a signal processing task similar to speech recognition.
- **Training with the processed data**. Once the data has been collected, we want to use to train sign language recognition models. Given the scope of our data collection thus far, we have created relatively small models which can classify 250 signs with roughly 85% accuracy. In the future, we would like to collect much larger datasets with much more impressive recognition capabilities, such as continuous sign recognition or even sign language generation.


The tools we have built to solve these problems include:

- [RecordTheseHands](https://github.com/Accessible-Technology-In-Sign/RecordTheseHands): an Android app which allows Deaf contributors to record themselves signing, then uploads those recordings, automatically segmented and labeled, to a bucket on Google Cloud.
- [WatchTheseHands](https://github.com/Accessible-Technology-in-Sign/WatchTheseHands): a frontend tool which allows volunteers to annotate the data as explained previously.
- A standard script to segment videos into individual MP4 clips.
- A standard script to process MediaPipe landmarks from the recorded videos.
- Miscellaneous data visualization tools to analyze problems with the data collection.
- A patchwork of TensorFlow or PyTorch repositories to train models based off of our collected data.

Signosure is a project to unify these disparate components into a single system, which hopefully can help us scale data collection to larger, more ambitious projects.

## Structure
The codebase is structured as follows:
- `build/`: Contains tools for deploying Signosure, such as Dockerfiles and Gradle components.
- `docs/`: Documentation should be saved here. Please read `docs/architecture.md` for more information on how the code in this repository is organized.
- `resources/`: Contains asset files,
