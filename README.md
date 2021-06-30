<p align="center">
  <a href="https://github.com/YahavBahat/LeakFinder" rel="noopener">
 <img width=400px height=250px src="https://securityintelligence.com/wp-content/uploads/2017/09/leaking-cloud-databases-and-servers-expose-over-1-billion-records.jpg" alt="Project logo"></a>
</p>

<h1 align="center">LeakFinder</h1>

---

<p align="center">🗄️💧 Find exposed and unsecured databases from a list of hosts. 🗄️💧
    <br> 
</p>



https://user-images.githubusercontent.com/19170083/123940542-f519c180-d9a1-11eb-9dfa-9d701ede267c.mp4



## 📝 Table of Contents
- [About](#about)
- [Getting Started](#getting_started)
- [Usage](#usage)
- [TODO](#TODO)
- [Contributing](#Contributing)
- [Authors](#authors)

## 🧐 About <a name = "about"></a>
Find interesting and exposed databases from a list of hosts. The program has the ability to filter and find interesting clusters by the its size, regex patterns, and keywords of your choosing. The program can also output the results into three different formats, including CSV, TXT, and JSONLINES.

## 🏁 Getting Started <a name = "getting_started"></a>

### Prerequisites
🐍 Python >= 3.6

Install the dependencies

```
pip3 install requirements.txt
```

## 🎈 Usage <a name="usage"></a>

Program supports the following Data Management System: Apache Cassandra, Elasticsearch, MongoDB, MySQL.
Get help using
```
python3 LeakFinder.py --help
```

### Providing Hosts

You can provide hosts using either one of the two mutually exclusive options: the `--hosts-file` or `-h` option, and the `--shodan-stream` or `-ss` option.
As the name implies, with the `--hosts-file` argument, you will have to pass a file of hosts, separated by a newline each.

Using the `--shodan-stream` or `-ss` option uses the Shodan Stream API, which returns a real-time stream of data collected by Shodan.
This option requires you to provide a Shodan API key in the `config.config` file.

### NMAP

The program matches every host to its suitable module by comparing the default port of the service/module (e.g., 9200 for ES) to the host's port from the hosts file. Sometimes, there are hosts with a port different from the module default one. Thus, the program cannot match the host to its suitable module.
This is where NMAP can help. We can find the service/module name using NMAP service scan, directly matching the host to the module.
You can enable this feature using the `--version-scan` or `-v` flag.
However, this could slow the program, so if one wants to exclude hosts with non-default ports, all he has to do is not to pass the `--version-scan` or `-v` flag.

### Filtering  Clusters

To exclude clusters who don't meet the specified standards, one would use the flag `--exclude-unmatched` or `-eu`.

#### Filtering Clusters by Size

To filter clusters by their size one should pass a dictionary, wrapped by single quotes, while it's values and its keys are wrapped in double quotes.
For example, if I want to get only the clusters which size are bigger than 100MB, I would pass
```
'{"bigger": 100000000}'
```
Notice that the size should be in Bytes.
If I would want to get the clusters which size is smaller than 7MB, I would pass
```
'{"smaller": 7000000}'
```
Note: Cassandra cluster's size won't be calculated and will be showen as `-1`.

#### Filtering Clusters by Regex Patterns

To filter clusters by regex patterns it is mandatory to provide a path to the regex patterns file using the `--patterns` or `p` option.
Every regex pattern/keyword should be separated by a newline.

In addition, you can choose where to try to match the regex patterns. Either in keyspaces/indexes names/databases names, or in tables/documents/collections names using the `--match-against` or `-m` option.
The following options are available: `[Databases names|Documents names|All]`. `--match-against` defaults to `All`.

### Ouput

In order to ouput the results to a file one would pass the `--output` or `-o` flag.
Note that output results are not in the same order of the hosts file.

#### Output Formats

There are three possible output format one could choose using the `--format` or `-f` option. Those are `[JSONLINES|CSV|TXT]`. Defaults to `TXT`.

The `--include-geo` or `-g` option makes it possible to include the country ISO code of the host.

### Authentication

If the authentication to the cluster fails, it's worth checking to see if the default password hasn't been changed.
The `--try-default` or `-t` flag tells the program to try authenticating with the default login credentials on authentication error or denied access exceptions.
Note: option available only in MySQL/Cassandra modules.

### Processes

It is possible to use multiprocessing and greatly speed-up the time execution of the program. To set the number of processes use the `--processes` option. Defaults to `1`.

You can pass the `--silent` flag to turn off terminal output.

### Getting Host Vulnerabilities

It is possible to getthe matched hosts'/clusters' for vulnerabilities using the Shodan API key. The query does **not** take scan or query credits.
To pass the shodan API key needs to insert the API key in the `config.config` file, in the value of the `api` key.
Afterwards, pass the `--shodan-vulns` or `-sv` flag to enable the feature.


`config.config` example file:
```
{"api": "APIKEY"}
```

### Example

To filter clusters by regex patterns and filter those whose size is bigger than 10MB, to include the host's country ISO code in output and to output to a JSONLINES (`.jsonl`) file, while using 12 processes, one would use this command:
```
python LeakFinder.py -h hosts.txt --patterns my_patterns.txt --size '{"smaller": 7000000}' -ig -o -f JSONLINES --processes 12 -ig
```

## 🚧 TODO: <a name="TODO"></a>
- [x] Add a Module for Apache Cassandra.
- [x] Multiprocessing.
- [x] Add an option to exclude unmatched clusters.
- [x] Get vulnerabilities using Shodan API.
- [x] Disable module API logging.
- [x] Continuously get a stream of hosts from Shodan Stream API.
- [ ] If authentication fails:
   - [x] (MYSQL/CASSANDRA) Authenticate with a default password.
   - [ ] Add an option to brute force from a wordlist.
- [ ] Refactor, document, and clean code.
- [ ] Add an option to add a custom module.
- [x] Add an option to match hosts whose port is different then the service's default port (e.g., host with port 9201, compared to the default port of ES, which is 9200) using NMAP.

## Contributing <a name="Contributing"></a>
Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change.

## ✍️ Authors <a name="authors"></a>
- [@YahavBahat](https://github.com/YahavBahat)
