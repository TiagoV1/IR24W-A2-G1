import re
from urllib.parse import urlparse, urlunparse, parse_qs, urljoin, urldefrag
from bs4 import BeautifulSoup



visited_urls = set()                            # List of all urls that have been visited
check_dynamic_traps_query = set()               # Set of sliced querys to check for dynamic traps
index_content = []                              # Index content of redirected URLs
visited_url_paths = dict()                      # Dictionary of paths and frequencies

global stop_words
stop_words = {'a', 'about', 'above', 'after', 'again', 'against', 'all', 'am', 'an', 'and', 'any', 'are', "aren't",
              'as', 'at', 'be', 'because', 'been', 'before', 'being', 'below', 'between', 'both', 'but', 'by',
              "can't", 'cannot', 'could', "couldn't", 'did', "didn't", 'do', 'does', "doesn't", 'doing', "don't",
              'down', 'during', 'each', 'few', 'for', 'from', 'further', 'had', "hadn't", 'has', "hasn't", 'have',
              "haven't", 'having', 'he', "he'd", "he'll", "he's", 'her', 'here', "here's", 'hers', 'herself', 'him',
              'himself', 'his', 'how', "how's", 'i', "i'd", "i'll", "i'm", "i've", 'if', 'in', 'into', 'is', "isn't",
              'it', "it's", 'its', 'itself', "let's", 'me', 'more', 'most', "mustn't", 'my', 'myself', 'no', 'nor',
              'not', 'of', 'off', 'on', 'once', 'only', 'or', 'other', 'ought', 'our', 'ours', 'ourselves', 'out',
              'over', 'own', 'same', "shan't", 'she', "she'd", "she'll", "she's", 'should', "shouldn't", 'so', 'some',
              'such', 'than', 'that', "that's", 'the', 'their', 'theirs', 'them', 'themselves', 'then', 'there',
              "there's", 'these', 'they', "they'd", "they'll", "they're", "they've", 'this', 'those', 'through', 'to',
              'too', 'under', 'until', 'up', 'very', 'was', "wasn't", 'we', "we'd", "we'll", "we're", "we've", 'were',
              "weren't", 'what', "what's", 'when', "when's", 'where', "where's", 'which', 'while', 'who', "who's",
              'whom', 'why', "why's", 'with', "won't", 'would', "wouldn't", 'you', "you'd", "you'll", "you're",
              "you've", 'your', 'yours', 'yourself', 'yourselves'}

#question 1 and question 2
unique_pages_found = dict()#http://www.ics.uci.edu#aaa and http://www.ics.uci.edu#bbb are the same URL. # link='', word_count=0
#question 3
words_and_frequency = dict()
#question 4
subdomain_and_numpages = dict() # subdomain as key, pages count as value


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
    
    #note that one megabyte is equal to 1024 * 1024
    global visited_urls
    extracted_links = set()
    # do not scrape urls which have already been scraped 
    if url in visited_urls:
        return []
    try: 
        # determine if the url is alive, has some text within a range o fless than 5 megabytes
        if resp.status == 200 and len(resp.raw_response.content) < 5 * 1024 * 1024:
                #get the page text content parsed out
                page_content = BeautifulSoup(resp.raw_response.content,'html.parser').get_text()
                #create tokens where tokens are letters of size 2 or larger coupled. 
                page_tokens = my_tokenize(page_content)
                #only if tokens are greater than 100, scrape for next links, this is our threshold for meaningful content
                if len(page_tokens) > 100:

                    # identify if the url is ics.uci.edu equally www.ics.uci.edu
                    create_subdomain_dictionary(url)
                    # use the tokens to update the word frequencies
                    update_word_frequency(page_tokens)

                    #Use urllib to create absolute links with urljoin
                    for link in BeautifulSoup(resp.raw_response.content, 'html.parser').find_all('a', href=True):                        
                        link_lead = link['href']
                        
                        """
                        #   urljoin takes two strings: lead url, follow url
                        #   if the follow url is an absolute link -> http(s)://www.abc.cd/xyz/, it returns the absolute link
                        #   if the follow url is a relative link -> a/abc/c OR /abc/c, it will create a new absolute link and return it
                        #       Case a/abc/c:
                        #           returns lead_url/a/abc/c
                        #       Case /abc/c:
                        #           returns lead_url/abc/c
                        #   More and thourough examples are here: https://stackoverflow.com/a/10893427
                        """
                        absolute_link = urljoin(url, link_lead) #Fragments are True by default
                        
                        # Ensure the link piece is not the url accessed, actual url and not in visited_url
                        if absolute_link not in url and absolute_link not in resp.url and absolute_link not in extracted_links and absolute_link not in visited_urls:
                            update_unique_pages_found(url, len(page_tokens))
                            if not is_path_limit_reached(absolute_link):
                                extracted_links.add(absolute_link)

        elif resp.status == 301 or resp.status == 302:
            # index urls that is redirect
            index_content.append(url)
        else:
            print("ERROR", resp.error)
    except Exception as err:
        print(f"Error processing URL {url}: {err}")
    finally:
        # even if an error is thrown we keep the urls and add them to the extracted links list.
        visited_urls.add(url)
        return list(extracted_links)


def my_tokenize(text_content):
    # this is Santiago's tokenize for assingmnet1 modefied to work for this assignment
    # Tokens are all alphanumeric characters
    global stop_words
    tokens_list = []
    for line in text_content.split('\n'):
        
        # spliting and turning all to lower case words (letters only) including hyphens 
        words = re.findall(r'[A-Za-z0-9]+(?:[\.\'\’\‘][A-Za-z0-9]+)*', line.lower())
        for index in range(len(words)):
            if "‘" in words[index] or "’" in words[index]:
                #replace the highphens in the words because they still do hold meaning   
                words[index] = words[index].replace("’", '\'')
                words[index] = words[index].replace("‘", '\'')
        #filter through the words for stop words, check if it is a number, and if it is less than two letters we don't want it to be a word
        words = [word for word in words if (word and word not in stop_words and not word.isnumeric() and len(word) > 1)]
        # update token list and return it
        tokens_list.extend(words)
    return tokens_list

def is_ics_uci_edu_subdomain(link):
    '''
    Checks if the subdomain is ics.uci.edu
    '''
    hostInfo = urlparse(link).hostname
    return re.match(r'\b(?:https?://)?(?:[a-zA-Z0-9-]+\.)?ics\.uci\.edu\b', hostInfo)

def is_path_limit_reached(link):
    '''
    Take the paths of the link without the fragment and check their frequencies
    Any path that is visited too much (Here 15) will be rejected from being added to the extracted link list
    '''
    
    global visited_url_paths
    link_to_process = urldefrag(link)[0]
    
    if link_to_process not in visited_url_paths:
        visited_url_paths[link_to_process] = 1
    elif visited_url_paths[link_to_process] < 15:
        visited_url_paths[link_to_process] += 1
    else:
        return True
    
    return False
    
def create_subdomain_dictionary(url):
    '''
    Parses the URL and checks to see if the hostname 
    is in the subdomain dictionary. If so, then the count
    for the subdomain increases count by 1, else, makes it a 
    key and sets it to 1. We now consider www.ics.uci.edu and
    ics.uci.edu the same.
    '''
    global subdomain_and_numpages
    parsed_hostname = urlparse(url).hostname

    if is_ics_uci_edu_subdomain(url):
        if parsed_hostname == "www.ics.uci.edu":
            if "ics.uci.edu" in subdomain_and_numpages:
                subdomain_and_numpages["ics.uci.edu"] = 1
            else:
                subdomain_and_numpages["ics.uci.edu"] += 1
        else:
            if parsed_hostname in subdomain_and_numpages:
                subdomain_and_numpages[parsed_hostname] += 1
            else:
                subdomain_and_numpages[parsed_hostname] = 1



def update_word_frequency(tokens):
    """
    takes a list of tokens and loops through it
    to create a word frequency dictionary
    if the word is not already in the dicitonary the
    count is set to 1 if it is the count is increased by one
    per occurance.
    """
    global words_and_frequency
    for token in tokens:
        if token not in words_and_frequency:
            words_and_frequency[token] = 1
        else:
            words_and_frequency[token] += 1


def update_unique_pages_found(link, other_word_count):
    """
    removes the fragment and if the page with the fragment removed
    has already been found then we increase the word count of that
    url by the new words. otherwise we just set it equal to the new
    words found. We consider pages with different fragements to be
    part of the same page/url.
    """
    global unique_pages_found 
    link = remove_fragment(link)
    if link in unique_pages_found:
        unique_pages_found[link] += other_word_count
    else:
        unique_pages_found[link] = other_word_count


def remove_fragment(url):
    """
    Takes a url and removes it's fragment
    """
    parsed_url = urlparse(url)
    url_without_fragment = parsed_url._replace(fragment='')
    reconstructed_url = urlunparse(url_without_fragment)
    return reconstructed_url


def calendar_trap_check(parsed):
    '''
    Checks for any URLs that are calendar traps.
    '''
    date_pattern = re.compile(r'\b(?:\d{1,4}[-/]\d{1,2}[-/]\d{1,4})\b|\b(?:\d{1,4}[-/]\d{1,4})\b')
    date_terms_pattern = re.compile(r'\b(?:past|event|day|week|month|quarter|year)\b')

    if re.search(date_pattern, parsed.path):
        return True
    if re.search(date_terms_pattern, parsed.path):
        return True
    if parsed.query != "":
        if re.search(date_pattern, parsed.query):
            return True
    return False


def dynamic_trap_check(parsed):
    '''
    Checks if URL is a Dynamic Trap but looking 
    into matching keywords.
    ''' 
    url_query = parsed.query
    if url_query != "":
        query_params = parse_qs(url_query)
        if len(query_params) > 7:
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
    path_segments = parsed.path.lower().split("/")
    path_segments = path_segments[1:]
    
    if len(path_segments) != len(set(path_segments)):               # Checks for any repeating paths
        print("Repeating path url trap: " + url)
        return True
        
    elif "session" in path_segments or "session" in parsed.query:   # Check for Session ID traps
        print("it is a session ID trap")
        return True

    return dynamic_trap_check(parsed) or calendar_trap_check(parsed) # Covers Dynamic URL Trap by checking for duplicate params
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
        pattern = re.compile(r"(?:http?://|https?://)?(?:\w+\.)?(?:ics|cs|informatics|stat)\.uci\.edu/")
        if re.match(pattern, url.lower()):  # Checks if URL matches the requirements
            if not is_trap(url, parsed):    # Check if the URL is a trap
                #Avoid user uploads
                if "wp-content/uploads" in parsed.path.lower():
                    return False
                
                #Avoid zip attachments
                if "zip-attachment" in parsed.path.lower():
                    return False

                #Avoid queries that are not id related
                if parsed.query != '' and "id" not in parsed.query.lower():
                    return False
                
                if "/files" in url or "/file" in url:
                    return False
                
                return not re.match(
                    r".*\.(css|js|bmp|gif|jpe?g|ico|php"
                    + r"|png|tiff?|mid|mp2|mp3|mp4"
                    + r"|wav|avi|mov|mpeg|ram|m4v|mkv|ogg|ogv|pdf"
                    + r"|ps|eps|tex|ppt|pptx|doc|docx|xls|xlsx|names|ppsx|pps"
                    + r"|data|dat|exe|bz2|tar|msi|bin|7z|psd|dmg|iso|ova"
                    + r"|epub|dll|cnf|tgz|sha1"
                    + r"|thmx|mso|arff|rtf|jar|csv|xml"
                    + r"|r|py|java|c|cc|cpp|h|svn|svn-base|bw|bigwig"
                    + r"|txt|odc|apk|img|war"
                    + r"|bam|bai|out|tab|edgecount|junction|ipynb|bib|lif"
                    + r"|rm|smil|wmv|swf|wma|zip|rar|gz)$", parsed.path.lower())
        return False

    
    except TypeError:
        print ("TypeError for ", parsed)
        raise


def generate_report_txt():
    with open('report.txt', 'w') as report:
        print("number of unique pages found: "+ str(len(unique_pages_found.keys())))

        report.write("------------------Report------------------"+ "\n")
        report.write("" + "\n")

        report.write("------------------QUESTION #1------------------"+"\n")
        report.write("Unique pages found: " + str(len(unique_pages_found.keys())) + "\n")
        report.write("" + "\n")
        report.write("" + "\n")

        report.write("------------------QUESTION #2------------------"+"\n")
        if unique_pages_found:
            max_url = max(unique_pages_found, key=unique_pages_found.get)
            report.write("URL with the largest word count: " + max_url + "\n")
        else:
            report.write("No URLs found with word count. The dictionary is empty.\n")
        report.write("" + "\n")
        report.write("" + "\n")

        report.write("------------------QUESTION #3------------------"+"\n")
        report.write("The following are the 50 most common words" + "\n")
        top_50_words = sorted(words_and_frequency.items(), key=lambda item: item[1], reverse=True)[:50]
        for word, frequency in top_50_words:
            report.write(f"Word: {word} - Frequency: {frequency}" + "\n")
        report.write("" + "\n")
        report.write("" + "\n")

        report.write("------------------QUESTION #4------------------"+"\n")
        report.write("Number of subdomains in the ics.uci.edu domain: " + str(len(subdomain_and_numpages.keys()))+ "\n")
        sorted_subdomains = sorted(subdomain_and_numpages.keys())
        for subdomain in sorted_subdomains:
            num_pages = subdomain_and_numpages[subdomain]
            report.write(f"{subdomain}, {num_pages}\n")
        report.write("" + "\n")
        report.write("" + "\n")