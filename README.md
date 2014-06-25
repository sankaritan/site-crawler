Site Crawler - website link tester
============

Yet another simple script that automatically crawls website and checks whether links are valid and that images are successfully loaded. Uses Selenium Webdriver and it is run by PyTest.

### Features

* crawls website links that match certain pattern
* reports broken links - target page request returns HTTP error
* reports invalid links - invalid characters in link url
* reports images that could not be loaded
* can ignore links with certain pattern
* supports basic authentication

### Execution

```bash
py.test site_crawler.py
````

### Required libraries

* Selenium Webdriver
* PyTest http://pytest.org (crawler uses Py.Test runner, such that it can be integrated into existing PyTest test-suite)
* Requests https://github.com/kennethreitz/requests

#### Installation using PIP

* ```pip install selenium pytest requests```

### Configuration

Variables need to be set in *site_crawler.cfg*. Required:

* base url (page crawler starts on)
* at least one acceptable url substring (typically domain such as "mypage.com"; script will crawl only links containing matching substrings)
* image time delay (defines how long to wait for images to be loaded; in seconds)
