# LeakFinder
🗄️💧 Find exposed and unsecured databases from a list of hosts. 🗄️💧 

## TODO:

- [x] Add a Module for Apache Cassandra.
- [x] Multiprocessing.
- [ ] Add an option to exclude unmatched clusters.
- [ ] Disable APIs logging.
- [ ] If authentication fails:
   - [ ] Authenticate with a default password.
   - [ ] Add an option to brute force from a wordlist.
- [ ] Refactor, comment, and clean code.
- [ ] Add arguments to the Module instance using dictionary/config file.
- [ ] Add an optional format to hosts.txt file `IP:PORT:MODULE_NAME` to be used to filter hosts to their suitable modules correctly, including hosts with non-default, unset ports.
