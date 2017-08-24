# ghJuicer
A tiny script that extracts metadata on millions of Github accounts.

Uses [GitHub API v3](https://developer.github.com/v3/). Run once and forget; it handles rate limits and internet connection errors without exiting. If stopped manually and run again, it will 
pick off from where it last stopped according to the last database row.

See my in-depth [blog post](http://tildeslash.io/2017/06/29/mass-github-account-metadata-extraction-automated/) for a full walkthrough on the thought process and development of the 
script from start to finish.

### Setup

`pip3 install --user -r requirements.txt`

### Usage

`./ghminer.py`
