# /usr/bin/env python
# -*- coding: utf-8 -*-
"""
    :copyright: (c) 2014 by Vojtech Burian
    :license: MIT, see LICENSE for more details.
"""
import ConfigParser
import time
import os

from requests.exceptions import HTTPError
import requests
from unittestzero import Assert
from selenium import webdriver


class TestSiteCrawler():
    """ automated website link & image checking bot """

    def setup_class(self):
        # load crawler variables
        config = ConfigParser.ConfigParser()
        config_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'site_crawler.cfg')
        config.read(config_file)
        test_vars = dict(config.defaults())

        # set crawler configuration variables
        self.default_implicit_wait = test_vars.get('default_implicit_wait')
        self.base_url = test_vars.get('base_url')
        self.acceptable_url_substrings = [item for item in test_vars.get('acceptable_url_substrings').split(';')]
        self.invalid_chars = [item for item in test_vars.get('invalid_chars').split(';')]
        self.ignore_url_substrings = [item for item in test_vars.get('ignore_url_substrings').split(';')]
        self.image_time_delay = int(test_vars.get('image_time_delay'))
        self.accept_certs = bool(test_vars.get('accept_ssl_certificates'))
        http_auth_username = test_vars.get('http_auth_username')
        http_auth_password = test_vars.get('http_auth_password')
        if http_auth_username == '' or http_auth_password == '':
            self.http_auth = None
        else:
            self.http_auth = (http_auth_username, http_auth_password)

        # crawler state variables
        self.links_visited = [self.base_url]
        self.invalid_urls = []
        self.error_links = []
        self.images_not_loaded = []

        # set browser capabilities
        capabilities = {}
        if self.accept_certs:
            capabilities['acceptSslCerts'] = True

        # start browser
        self.driver = webdriver.Chrome(desired_capabilities=capabilities)
        self.driver.get(self.base_url)

    def teardown_class(self):
        self.driver.quit()

    def test_unleash_bot(self):
        """ tests links on page """
        self.check_links()
        self.report_failures()

    def check_links(self):
        """ recursively checks links on websites and checks whether images have been loaded properly """
        links_objects = self.driver.find_elements_by_tag_name('a')
        valid_links_on_page = []
        # collect valid links on page for testing
        for link in links_objects:
            url = link.get_attribute('href')
            if url is not None and self.is_url_valid(url):
                valid_links_on_page.append(link.get_attribute('href'))

        # start testing each link with valid url
        for link in valid_links_on_page:
            if link not in self.links_visited:
                self.links_visited.append(link)
                # test link if request does not return invalid response
                if self.is_link_response_ok(link):
                    print 'Visiting: ' + link
                    self.driver.get(link)
                    self.wait_for_page_to_load()
                    self.check_images()
                    # recursively crawl test links found on this page
                    self.check_links()
                    self.driver.back()

    def report_failures(self):
        """ makes assertion fail if there had been any kind of failures reported """
        fail_message = ''
        if len(self.invalid_urls) > 0:
            fail_message += 'Invalid URLs detected: ' + str(self.invalid_urls) + '\n'
        if len(self.images_not_loaded) > 0:
            fail_message += 'Following images were not loaded: ' + str(self.images_not_loaded) + '\n'
        if len(self.error_links) > 0:
            fail_message += 'Following links returned bad status codes: ' + str(self.error_links)
        if fail_message != '':
            Assert.fail(fail_message)
        print 'Visited links: ' + str(self.links_visited)

    def is_url_valid(self, url):
        """ checks whether url is valid and whether browser should try to load it """
        url_valid = True
        # excludes urls with values not required for testing
        for invalid_item in self.ignore_url_substrings:
            if invalid_item in url:
                url_valid = False
        # excludes urls that do not contain acceptable substrings (links leading to different domains)
        if url_valid:
            url_acceptable = False
            for substring in self.acceptable_url_substrings:
                if substring in url:
                    url_acceptable = True
            if not url_acceptable:
                url_valid = False
        # reports urls with invalid characters
        if url_valid:
            for item in self.invalid_chars:
                if item in url and url not in self.invalid_urls:
                    self.invalid_urls.append(url)
                    url_valid = False
        # reports empty urls with invalid characters
        if url_valid and url == '':
            if url not in self.invalid_urls:
                self.invalid_urls.append(url)
            url_valid = False
        return url_valid

    def is_link_response_ok(self, url):
        """ checks if request to link does not return invalid error code """
        response = requests.get(url, auth=self.http_auth, verify=(not self.accept_certs))
        is_ok = True
        try:
            response.raise_for_status()
        except HTTPError:
            self.error_links.append(url)
            is_ok = False
        return is_ok

    def wait_for_page_to_load(self):
        """ waits for page to load properly; important mainly for checking images """
        # time.sleep(self.image_time_delay)
        self.driver.implicitly_wait(self.default_implicit_wait)

    def check_images(self):
        """ checks all images on the pages and verifies if they have been properly loaded;
         if some images are not loaded yet, script waits for certain amount of time and then tries again """
        images_not_loaded = self.check_images_are_loaded()
        if len(images_not_loaded) != 0:
            time.sleep(self.image_time_delay)
            images_not_loaded = self.check_images_are_loaded()
            if len(images_not_loaded) != 0:
                self.images_not_loaded.extend(images_not_loaded)

    def check_images_are_loaded(self):
        """ checks all images on the pages and verifies if they have been properly loaded """
        images_not_loaded = []
        for image in self.driver.find_elements_by_tag_name('img'):
            script = 'return arguments[0].complete && typeof arguments[0].naturalWidth' \
                     ' != "undefined" && arguments[0].naturalWidth > 0'
            image_loaded = bool(self.driver.execute_script(script, image))
            if not image_loaded:
                if image.get_attribute('src') is not None:
                    images_not_loaded.append(self.driver.title + ': ' + str(image.get_attribute('src')))
        return images_not_loaded