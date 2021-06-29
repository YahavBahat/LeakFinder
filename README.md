<p align="center">
  <a href="" rel="noopener">
 <img width=400px height=250px src="https://securityintelligence.com/wp-content/uploads/2017/09/leaking-cloud-databases-and-servers-expose-over-1-billion-records.jpg" alt="Project logo"></a>
</p>

<h1 align="center">LeakFinder</h1>

---

<p align="center">🗄️💧 Find exposed and unsecured databases from a list of hosts. 🗄️💧
    <br> 
</p>

## 📝 Table of Contents
- [About](#about)
- [Getting Started](#getting_started)
- [Usage](#usage)
- [TODO](#TODO)
- [Contributing](Contributing)
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
Get help using
```
python3 LeakFinder.py --help
```

`--hosts-file` or `-h` is required.

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

### Vulnerability Scanning

It is possible to scan the matched hosts/clusters for vulnerabilities using the Shodan API key. The query does **not** take scan or query credits.
To pass the shodan API key one can either use the command-line argument `--shodan` or `-sn`, or alternatively put insert the API key in the `config.config` file, in the value of the `api` key.


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
- [ ] (MYSQL/CASSANDRA) If authentication fails:
   - [x] Authenticate with a default password.
   - [ ] Add an option to brute force from a wordlist.
- [ ] Refactor, document, and clean code.
- [ ] Add an option to add a custom module.
- [ ] Add an optional format to hosts.txt file `IP:PORT:MODULE_NAME` to be used to filter hosts to their suitable modules correctly, including hosts with non-default, unset ports.

## Contributing <a name="Contributing"></a>
Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change.

## ✍️ Authors <a name="authors"></a>
- [@YahavBahat](https://github.com/YahavBahat)
