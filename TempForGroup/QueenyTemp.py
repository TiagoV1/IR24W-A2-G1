import re
from urllib.parse import urlparse
from urllib import robotparser
import time


visted_urls = []    # List of all urls that have been visited
check_dynamic_traps_query = []    # List of sliced querys to check for dynamic traps


def scraper(url, resp):
    links = extract_next_links(url, resp)
    return [link for link in links if is_valid(link)]

def extract_next_links(url, resp):
    # Implementation required.
    # url: the URL that was used to get the page
    # resp.url: the actual url of the page
    # resp.status: the status code returned by the server. 200 is OK, you got the page. Other numbers mean that there was some kind of problem.
    # resp.error: when status is not 200, you can check the error here, if needed.
    # resp.raw_response: this is where the page actually is. More specifically, the raw_response has two parts:
    #         resp.raw_response.url: the url, again
    #         resp.raw_response.content: the content of the page!
    # Return a list with the hyperlinks (as strings) scrapped from resp.raw_response.content
    return list()


def read_robots(url,  user_agent='*'):
    '''
    Reads robots.txt and deems if it is 
    allowed to be crawled to.
    '''
    rp = robotparser.RobotFileParser()      # Parses robot.txt
    rp.set_url(url + '/robots.txt')         # Set the URL of the robots.txt file
    rp.read()                               # Read and parse the robots.txt file
    return rp.can_fetch(user_agent, url)    # Searches robots.txt and returns boolean if site can be crawled


def is_trap(url, parsed):
    '''
    Checks if url is a trap, returns true if so
    else returns false
    '''
    # Traps:
    #   Infinite Loop Trap: may have to be implemented into extract_next_links
    #   Duplicate URL Traps
    #   Calendar Traps
    #       Check for repeats
    #   Some Dynamic Traps

    if re.match(r'(\w+)(?:/\1)+', url.path):     # Covers Calendar Trap by checking repeating paths
        return True
    
    elif url in visted_urls:                    # Covers Duplicate URL Traps by checking already visited URLs
        return True

    else:                                       # Covers Dynamic URL Trap by checking for duplicate params
        url_query = parsed.query
        index = url_query.index("=")
        new_url_query = parsed.scheme + parsed.netloc + parsed.path + "?" + url_query[0:index]

        if new_url_query in check_dynamic_traps_query:
            return True
        else:
            check_dynamic_traps_query.append(new_url_query)
            return False


def is_valid(url):
    # Decide whether to crawl this url or not. 
    # If you decide to crawl it, return True; otherwise return False.
    # There are already some conditions that return False.
    # *.ics.uci.edu/*
    # *.cs.uci.edu/*
    # *.informatics.uci.edu/*
    # *.stat.uci.edu/*

    try:
        parsed = urlparse(url)
        pattern = re.compile(r"(?:http?://|https?://)?(?:ics|cs|informatics|stat)\.uci\.edu\/S*")

        if parsed.scheme in set(["http", "https"]) and re.match(pattern, url.lower()):
            if read_robots(url):
                if not is_trap(url, parsed):
                    return True

                

        # return not re.match(
        #     r".*.(css|js|bmp|gif|jpe?g|ico"
        #     + r"|png|tiff?|mid|mp2|mp3|mp4"
        #     + r"|wav|avi|mov|mpeg|ram|m4v|mkv|ogg|ogv|pdf"
        #     + r"|ps|eps|tex|ppt|pptx|doc|docx|xls|xlsx|names"
        #     + r"|data|dat|exe|bz2|tar|msi|bin|7z|psd|dmg|iso"
        #     + r"|epub|dll|cnf|tgz|sha1"
        #     + r"|thmx|mso|arff|rtf|jar|csv"
        #     + r"|rm|smil|wmv|swf|wma|zip|rar|gz)$", parsed.path.lower())
            
        return False
    
    except TypeError:
        print ("TypeError for ", parsed)
        raise
