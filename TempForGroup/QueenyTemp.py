import re
from urllib.parse import urlparse
from urllib import robotparser


visited_urls = []                        # List of all urls that have been visited
check_dynamic_traps_query = set()        # Set of sliced querys to check for dynamic traps
date_terms = set("day", "month", "year") # Set of date terms

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


def dynamic_trap_check(url, parsed):
    '''
    Checks if URL is a Dynamic Trap but looking 
    into matching keywords.
    ''' 
    url_query = parsed.query
    index = url_query.index("=")
    new_url_query = parsed.scheme + "://" + parsed.netloc + parsed.path + "?" + url_query[0:index]  # Rebuilds the url but with only the first parameter

    if new_url_query in check_dynamic_traps_query:              # Checks if the URL is already been crawled through
        return True
    else:
        check_dynamic_traps_query.add(new_url_query)
        return False


def calendar_trap_check(parsed, path_segments):
    '''
    Checks for any URLs that are calendar traps.
    '''
    date_pattern = re.compile(r'/(?:(?:\d{4}-\d{2}-\d{2})|(?:\d{4}-\d{2})|(?:\d{2}-\d{2}-\d{4})|(?:\d{1,2}/\d{1,2}/\d{2,4}))/')

    if re.match(date_pattern, parsed.path) or bool(set(path_segments) & date_terms):    # Check if there is a number date format in the URL
        return True
    elif "past" in parsed.query:    # Checks for evenDisplay=past to avoid going too deep into calendar
        return True
    return False


def is_trap(url, parsed):
    '''
    Checks if url is a trap, returns true if so
    else returns false.
    Covers:
        - Duplicate URL Traps
        - Repeated Paths Trap (ICS Calendar)
        - Session ID Trap
        - Dynamic URL Trap
    '''
    date_pattern = re.compile(r'\b(?:\d{2}/\d{2}/\d{4}|\d{4}-\d{2}-\d{2}|[a-zA-Z]{3}/\d{2}/[a-zA-Z]{3})\b')
    path_segments = parsed.path.split("/")
    
    if url in visited_urls:                                         # Covers Duplicate URL Traps by checking already visited URLs
        return True  

    elif len(path_segments) != len(set(path_segments)):             # Checks for any repeating paths
        return True
        
    elif "session" in path_segments or "session" in parsed.query:   # Check for Session ID traps
        return True

    return dynamic_trap_check(url, parsed) or calendar_trap_check(parsed, path_segments)  # Covers Dynamic URL Trap by checking for duplicate params
                                                                                          # and Covers Calendar Trap by checking repeating paths


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

        if parsed.scheme in set(["http", "https"]) and re.match(pattern, url.lower()):  # Checks if URL matches the requirements
            if read_robots(url):                # Checks if robots.txt allows crawlers
                if not is_trap(url, parsed):    # Check if the URL is a trap
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
