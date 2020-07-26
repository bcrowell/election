default:
	@echo "Running the simulation with defaults. Any command-line arguments will be ignored."
	python3 election.py >current_results.txt
	cat current_results.txt

