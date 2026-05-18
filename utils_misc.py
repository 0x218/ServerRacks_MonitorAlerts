def print_execution_seconds(start_time, end_time, ):
    execution_seconds = end_time - start_time
    execution_minutes = execution_seconds / 60

    print(
        f"Total Execution Time: "
        f"{execution_seconds:.2f} seconds "
        f"({execution_minutes:.2f} minutes)"
    )
