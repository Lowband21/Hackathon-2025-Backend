from typing import Dict, List, TypedDict, Optional

class Answer(TypedDict):
    domain: str
    facet: Optional[int]
    score: float

class FacetResult(TypedDict):
    score: float
    count: int
    result: str

class DomainResult(TypedDict):
    score: float
    count: int
    result: str
    facet: Dict[str, FacetResult]

def process_answers(answers: List[Answer]) -> Dict[str, DomainResult]:
    """
    Process a list of answers and calculate domain and facet results.
    
    Args:
        answers: List of Answer objects with domain, facet, and score
        
    Returns:
        Dictionary mapping domains to their results
    """
    result: Dict[str, DomainResult] = {}

    for answer in answers:
        domain = answer['domain']
        if domain not in result:
            result[domain] = {'score': 0, 'count': 0, 'result': 'neutral', 'facet': {}}
        
        domain_result = result[domain]
        domain_result['score'] += answer['score']
        domain_result['count'] += 1

        if 'facet' in answer and answer['facet'] is not None:
            facet = str(answer['facet'])
            if facet not in domain_result['facet']:
                domain_result['facet'][facet] = {'score': 0, 'count': 0, 'result': 'neutral'}
            
            facet_result = domain_result['facet'][facet]
            facet_result['score'] += answer['score']
            facet_result['count'] += 1

    # Calculate results for domains and facets
    for domain_result in result.values():
        domain_result['result'] = calculate_result(domain_result['score'], domain_result['count'])
        for facet_result in domain_result['facet'].values():
            facet_result['result'] = calculate_result(facet_result['score'], facet_result['count'])

    return result

def calculate_result(score: float, count: int) -> str:
    """
    Calculate the result category based on average score.
    
    Args:
        score: Total score
        count: Number of answers
        
    Returns:
        'high', 'neutral', or 'low'
    """
    avg_score = score / count
    if avg_score > 3.5:
        return 'high'
    elif avg_score < 2.5:
        return 'low'
    return 'neutral'

def process_question_answers(user_answers: Dict[int, int], questions: List[Dict]) -> List[Answer]:
    """
    Process raw user answers to convert to the Answer format needed for calculation
    
    Args:
        user_answers: Dictionary mapping question index to answer value (1-5)
        questions: List of question objects from the personality_questions.json
        
    Returns:
        List of Answer objects with domain, facet, and score
    """
    answers: List[Answer] = []
    
    for question_id, answer_value in user_answers.items():
        try:
            question_idx = int(question_id)
            if question_idx < 0 or question_idx >= len(questions):
                continue
                
            question = questions[question_idx]
            domain = question['domain']
            facet = int(question['facet'])
            
            # Handle reversed scoring (keyed as "minus")
            score = float(answer_value)
            if question['keyed'] == 'minus':
                score = 6 - score  # Reverse the score (1→5, 2→4, etc.)
            
            answers.append({
                'domain': domain,
                'facet': facet,
                'score': score
            })
        except (ValueError, KeyError, IndexError):
            # Skip invalid answers
            continue
    
    return answers

def get_text_results(results: Dict[str, DomainResult], test_structure: List[Dict]) -> Dict[str, Dict]:
    """
    Get the text descriptions for the calculated results
    
    Args:
        results: Dictionary of domain results
        test_structure: List of domain structures from personality_test.json
        
    Returns:
        Dictionary mapping domains to their text results
    """
    text_results = {}
    
    # Map domain codes to their positions in the test_structure
    domain_map = {domain['domain']: i for i, domain in enumerate(test_structure)}
    
    for domain_code, domain_result in results.items():
        domain_idx = domain_map.get(domain_code)
        if domain_idx is None:
            continue
            
        domain_data = test_structure[domain_idx]
        
        # Find the matching result text for the domain
        domain_text = None
        for result_text in domain_data['results']:
            if result_text['score'] == domain_result['result']:
                domain_text = result_text['text']
                break
        
        # Get facet descriptions
        facet_texts = {}
        for facet_num, facet_result in domain_result['facet'].items():
            facet_num = int(facet_num)
            if facet_num < 1 or facet_num > len(domain_data['facets']):
                continue
                
            facet_data = domain_data['facets'][facet_num - 1]
            facet_texts[facet_num] = {
                'title': facet_data['title'],
                'description': facet_data['text'],
                'result': facet_result['result']
            }
        
        text_results[domain_code] = {
            'title': domain_data['title'],
            'description': domain_data['shortDescription'],
            'result_text': domain_text,
            'facets': facet_texts
        }
    
    return text_results
