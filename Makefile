default:
	@echo "Running the simulation with defaults. Any command-line arguments will be ignored."
	python3 election.py >current_results.txt
	cat current_results.txt

polls:
	curl -o a.csv https://projects.fivethirtyeight.com/polls-page/president_polls.csv
	mv a.csv president_polls.csv
	./polls.py

