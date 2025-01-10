import json
from typing import List, Dict, Any
from collections import Counter, defaultdict
from rich.console import Console
from rich.table import Table
from aws_interaction import download_json_from_s3
from hash_manager import HashManager
from tests import *

top_weights = {
    'Authenticity':0.2,
    'Quality':0.7,
    'Uniquness':0.1
}
test_weights = {
    'Time_Minimums':0.1,
    'Time_Correlation':0.2,
    'Time_Distribution':0.1,
    'Repeat_Anwsers':0.15,
    'Both_Sides':0.15,
    'Model_Distribution':0.05,
    'Poisin_Data':0.25,
}



#thoughts,
#we shouldnt pass model name down to the browser, should use the id to do a lookup in validation to see what the model is. people could read the data and auto choose better model

def Score() -> float:
    pass

def Authenticity() -> float:
    pass

def Quality(data_list: List[Dict[str, Any]]) -> float:
    #all tests
    #average time taken is less than 5 seconds
    #time correlates to time
    #distribution in times taken
    #anwsering repeat questions the same way,Check for duplicate uniqueIDs with different 'chosen' values
    #choosing option 1 and option 2, Analyze the distribution of 'chosen' values
    #Check for model bias in 'chosen' responses, might be dumb we expect 70b to do better than 7b so will not be even distribution
    #Perform randomness test using Chi-squared test, make sure there is some distribution in what gets chosen
    #Check if it is poisoned data and make sure that they chose the same response
    # 8 seperate tests
    report = {
        'Time_Minimums':Time_Minimums(data_list),
        'Time_Correlation':Character_Timing(data_list),
        'Time_Distribution':Time_Distribution(data_list),
        'Repeat_Anwsers':Duplicate_ID_Check(data_list),
        'Both_Sides':Choice_Distribution(data_list),
        'Model_Distribution':Model_Bias(data_list),
        'Poisin_Data':Poison_Consistency(data_list),
        'score':0
    }
    report['score'] = sum(test_weights[test] * report[test]['score'] for test in test_weights)
    print(report)
    display_report(report)
    return report['score']

def Uniquness(data_list: List[Dict[str, Any]]) -> float:
    hash_manager = HashManager(bucket_name="vanatensordlp", remote_file_key="verified_hashes/hashes.json")
    hash_exists = hash_manager.generate_hash(data_list) in hash_manager.get_remote_hashes()
    if hash_exists:
        return 0.0
    else:
        hash_manager.add_hash(hash_manager.generate_hash(data_list))
        return 1.0

def validate(data_list: List[Dict[str, Any]]) -> dict:
    #correlation of size of text, to time taken,
    #return floats like larry sent
    #{
    #    score:0.67, // weighted avg of below, ie authenticity*0.2, quality *0.7, uniqueness *0.1
    #    authenticity:0.567, // would be nice to do some kind of hash coming from the browser to ensure authenticity, 
    #    quality:7689, #assesment below
    #    uniquness:678, # will be a 0,1 based on storing hashes
    #    attributes:{},
    #}

    return {
        "score":Quality(data_list),
        "authenticity":"",#Authenticity(data_list),
        "uniquness":Uniquness(data_list)
    }


def sample_validate():
    # Sample data
    sample_data_list = json.load(open('/Users/dylanhubble/Desktop/1731597764681.json'))
    return validate(sample_data_list)

def display_report(report: dict) -> None:
    console = Console()
    
    # Create main score table
    main_score = Table(title="[bold magenta]Quality Assessment Report[/bold magenta]", 
                      show_header=True,
                      header_style="bold cyan")
    main_score.add_column("Overall Score", justify="center", style="bold")
    main_score.add_row(f"{report['score']:.2%}")
    
    # Create detailed results table
    results = Table(show_header=True, header_style="bold cyan", 
                   title="[bold magenta]Detailed Test Results[/bold magenta]")
    results.add_column("Test", style="bold green")
    results.add_column("Score", justify="center")
    results.add_column("Status", justify="center")
    results.add_column("Details", justify="left")

    # Test result emojis
    PASS = "✅"
    PARTIAL = "⚠️"
    FAIL = "❌"

    # Mapping of score ranges to status
    def get_status(score):
        if score >= 0.8: return (PASS, "green")
        if score >= 0.4: return (PARTIAL, "yellow")
        return (FAIL, "red")

    # Add each test result
    for test_name, data in report.items():
        if test_name == 'score':
            continue
            
        score = data['score']
        status_emoji, color = get_status(score)
        
        # Format comments as a single string with line breaks
        comments = '\n'.join(data['comments'])
        
        results.add_row(
            test_name.replace('_', ' '),
            f"[{color}]{score:.2%}[/{color}]",
            status_emoji,
            comments
        )

    # Print the report
    console.print()
    console.print(main_score, justify="center")
    console.print()
    console.print(results)
    console.print()

    # Add a summary footer
    if report['score'] >= 0.8:
        console.print("[bold green]Overall Assessment: EXCELLENT[/bold green]", justify="center")
    elif report['score'] >= 0.6:
        console.print("[bold yellow]Overall Assessment: GOOD[/bold yellow]", justify="center")
    elif report['score'] >= 0.4:
        console.print("[bold yellow]Overall Assessment: FAIR[/bold yellow]", justify="center")
    else:
        console.print("[bold red]Overall Assessment: NEEDS IMPROVEMENT[/bold red]", justify="center")

sample_validate()