# Running this example


```bash
pip install curdling
curd install lineup

# clone the repo
git clone git@github.com/weedlabs/lineup.git

# go to the repo
cd lineup

# run lineup

lineup downloader run &

# push stuff to lineup

lineup downloader push '{"url": "http://github.com"}'
lineup downloader push '{"url": "http://twitter.com"}'

# when you are done:

lineup downloader stop
```

Learn more in the [documentation](http://weedlabs.github.io/lineup)
