"""
Sample workflow: Code Review Mini-Agent

A simple rule-based code review workflow that:
1. Extracts functions from code
2. Checks complexity
3. Detects issues
4. Suggests improvements
5. Loops until quality score meets threshold
"""
import re
from typing import Dict, Any, Union


async def extract_functions(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract function definitions from code.
    
    Updates state with:
    - functions: list of extracted function info
    - function_count: number of functions found
    """
    code = state.get("code", "")
    
    # Simple regex to find function definitions
    # Matches: def function_name(...):
    pattern = r'def\s+(\w+)\s*\([^)]*\)\s*:'
    matches = re.finditer(pattern, code)
    
    functions = []
    for match in matches:
        func_name = match.group(1)
        start_pos = match.start()
        # Find the end of the function (next def or end of code)
        next_def = code.find("def ", start_pos + 1)
        if next_def == -1:
            end_pos = len(code)
        else:
            end_pos = next_def
        
        func_code = code[start_pos:end_pos]
        lines = func_code.count('\n') + 1
        
        functions.append({
            "name": func_name,
            "start": start_pos,
            "end": end_pos,
            "lines": lines,
            "code": func_code
        })
    
    state["functions"] = functions
    state["function_count"] = len(functions)
    state["extraction_complete"] = True
    
    return state


async def check_complexity(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Check complexity of extracted functions.
    
    Updates state with:
    - complexity_scores: dict mapping function names to complexity scores
    - max_complexity: highest complexity score
    - avg_complexity: average complexity score
    """
    functions = state.get("functions", [])
    complexity_scores = {}
    
    for func in functions:
        func_code = func.get("code", "")
        func_name = func.get("name", "unknown")
        
        # Simple complexity metrics:
        # - Lines of code
        # - Number of if/else/for/while statements
        # - Nesting depth
        
        lines = func.get("lines", 0)
        if_count = func_code.count(" if ")
        for_count = func_code.count(" for ")
        while_count = func_code.count(" while ")
        control_flow = if_count + for_count + while_count
        
        # Calculate nesting depth (count indentation levels)
        max_indent = 0
        for line in func_code.split('\n'):
            stripped = line.lstrip()
            if stripped:
                indent = len(line) - len(stripped)
                max_indent = max(max_indent, indent // 4)  # Assuming 4-space indentation
        
        # Simple complexity score
        complexity = lines + (control_flow * 2) + (max_indent * 3)
        complexity_scores[func_name] = complexity
    
    if complexity_scores:
        state["complexity_scores"] = complexity_scores
        state["max_complexity"] = max(complexity_scores.values())
        state["avg_complexity"] = sum(complexity_scores.values()) / len(complexity_scores)
    else:
        state["max_complexity"] = 0
        state["avg_complexity"] = 0
    
    state["complexity_checked"] = True
    
    return state


async def detect_issues(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Detect issues in the code based on complexity and patterns.
    
    Updates state with:
    - issues: list of detected issues
    - issue_count: number of issues found
    """
    functions = state.get("functions", [])
    complexity_scores = state.get("complexity_scores", {})
    issues = []
    
    # Check for high complexity
    for func in functions:
        func_name = func.get("name", "unknown")
        complexity = complexity_scores.get(func_name, 0)
        func_code = func.get("code", "")
        
        if complexity > 50:
            issues.append({
                "type": "high_complexity",
                "function": func_name,
                "severity": "high",
                "message": f"Function '{func_name}' has high complexity ({complexity})"
            })
        
        # Check for long functions
        if func.get("lines", 0) > 50:
            issues.append({
                "type": "long_function",
                "function": func_name,
                "severity": "medium",
                "message": f"Function '{func_name}' is too long ({func.get('lines')} lines)"
            })
        
        # Check for deep nesting
        max_indent = 0
        for line in func_code.split('\n'):
            stripped = line.lstrip()
            if stripped:
                indent = len(line) - len(stripped)
                max_indent = max(max_indent, indent // 4)
        
        if max_indent > 4:
            issues.append({
                "type": "deep_nesting",
                "function": func_name,
                "severity": "medium",
                "message": f"Function '{func_name}' has deep nesting (level {max_indent})"
            })
        
        # Check for missing docstrings
        if '"""' not in func_code and "'''" not in func_code:
            issues.append({
                "type": "missing_docstring",
                "function": func_name,
                "severity": "low",
                "message": f"Function '{func_name}' is missing a docstring"
            })
    
    state["issues"] = issues
    state["issue_count"] = len(issues)
    state["issues_detected"] = True
    
    return state


async def suggest_improvements(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Suggest improvements based on detected issues.
    
    Updates state with:
    - suggestions: list of improvement suggestions
    - quality_score: calculated quality score (0-100)
    """
    issues = state.get("issues", [])
    function_count = state.get("function_count", 1)
    suggestions = []
    
    # Generate suggestions based on issues
    for issue in issues:
        issue_type = issue.get("type")
        func_name = issue.get("function")
        
        if issue_type == "high_complexity":
            suggestions.append({
                "function": func_name,
                "suggestion": f"Consider breaking down '{func_name}' into smaller functions",
                "priority": "high"
            })
        elif issue_type == "long_function":
            suggestions.append({
                "function": func_name,
                "suggestion": f"Split '{func_name}' into multiple smaller functions",
                "priority": "medium"
            })
        elif issue_type == "deep_nesting":
            suggestions.append({
                "function": func_name,
                "suggestion": f"Reduce nesting in '{func_name}' using early returns or guard clauses",
                "priority": "medium"
            })
        elif issue_type == "missing_docstring":
            suggestions.append({
                "function": func_name,
                "suggestion": f"Add a docstring to '{func_name}' explaining its purpose",
                "priority": "low"
            })
    
    # Calculate quality score
    # Start with 100 and deduct points for issues
    quality_score = 100
    for issue in issues:
        severity = issue.get("severity", "low")
        if severity == "high":
            quality_score -= 10
        elif severity == "medium":
            quality_score -= 5
        else:
            quality_score -= 2
    
    # Normalize by function count
    if function_count > 0:
        quality_score = max(0, quality_score / function_count)
    
    # Ensure score is between 0 and 100
    quality_score = max(0, min(100, quality_score))
    
    state["suggestions"] = suggestions
    state["quality_score"] = quality_score
    state["suggestions_generated"] = True
    
    return state


async def check_quality_threshold(state: Dict[str, Any]) -> Union[Dict[str, Any], str]:
    """
    Check if quality score meets threshold and decide whether to loop.
    
    This node can return "repeat" to loop back to earlier nodes,
    or continue to completion.
    
    Updates state with:
    - threshold_met: boolean indicating if threshold is met
    """
    quality_score = state.get("quality_score", 0)
    threshold = state.get("quality_threshold", 70)  # Default threshold
    
    if quality_score >= threshold:
        state["threshold_met"] = True
        state["review_complete"] = True
        return state  # Continue to next node (completion - no edge means done)
    else:
        state["threshold_met"] = False
        # Return "goto:" to jump back to suggest_improvements for another iteration
        # In a real scenario, this might loop back to detect_issues
        # after applying suggestions
        return "goto:suggest_improvements"

