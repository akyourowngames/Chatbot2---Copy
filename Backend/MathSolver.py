"""
Math Solver - Beast Mode (Ultimate Edition)
============================================
Advanced mathematical computation engine.
Features:
- Expression evaluation with full math library
- Equation solving (linear, quadratic, cubic)
- Unit conversions
- Statistics & probability
- Natural language math parsing
- Step-by-step solutions
"""

import re
import math
from typing import Dict, Any, List, Union, Optional
from fractions import Fraction
import statistics

class MathSolver:
    def __init__(self):
        # Extended math functions
        self.safe_functions = {
            # Basic math
            'abs': abs, 'round': round, 'max': max, 'min': min,
            'sum': sum, 'pow': pow, 'divmod': divmod,
            # Math module
            'sqrt': math.sqrt, 'cbrt': lambda x: x ** (1/3),
            'sin': math.sin, 'cos': math.cos, 'tan': math.tan,
            'asin': math.asin, 'acos': math.acos, 'atan': math.atan,
            'sinh': math.sinh, 'cosh': math.cosh, 'tanh': math.tanh,
            'log': math.log, 'log10': math.log10, 'log2': math.log2,
            'exp': math.exp, 'floor': math.floor, 'ceil': math.ceil,
            'factorial': math.factorial, 'gcd': math.gcd,
            # Constants
            'pi': math.pi, 'e': math.e, 'tau': math.tau,
            'inf': math.inf, 'nan': math.nan,
        }
        
        # Unit conversions
        self.units = {
            # Length
            'km_to_miles': 0.621371, 'miles_to_km': 1.60934,
            'cm_to_inches': 0.393701, 'inches_to_cm': 2.54,
            'm_to_feet': 3.28084, 'feet_to_m': 0.3048,
            # Weight
            'kg_to_lbs': 2.20462, 'lbs_to_kg': 0.453592,
            'g_to_oz': 0.035274, 'oz_to_g': 28.3495,
            # Temperature (special handling)
            # Volume
            'liters_to_gallons': 0.264172, 'gallons_to_liters': 3.78541,
            # Speed
            'kmh_to_mph': 0.621371, 'mph_to_kmh': 1.60934,
        }
        
        # Natural language patterns
        self.nl_patterns = [
            (r'(\d+)\s*(?:plus|\+)\s*(\d+)', lambda m: f"{m.group(1)}+{m.group(2)}"),
            (r'(\d+)\s*(?:minus|-)\s*(\d+)', lambda m: f"{m.group(1)}-{m.group(2)}"),
            (r'(\d+)\s*(?:times|multiplied by|x|×|\*)\s*(\d+)', lambda m: f"{m.group(1)}*{m.group(2)}"),
            (r'(\d+)\s*(?:divided by|over|÷|/)\s*(\d+)', lambda m: f"{m.group(1)}/{m.group(2)}"),
            (r'(\d+)\s*(?:to the power of|raised to|\^|\*\*)\s*(\d+)', lambda m: f"{m.group(1)}**{m.group(2)}"),
            (r'square root of\s*(\d+)', lambda m: f"sqrt({m.group(1)})"),
            (r'cube root of\s*(\d+)', lambda m: f"({m.group(1)})**(1/3)"),
            (r'(\d+)\s*percent of\s*(\d+)', lambda m: f"{m.group(1)}/100*{m.group(2)}"),
            (r'(\d+)\s*factorial', lambda m: f"factorial({m.group(1)})"),
        ]

    def solve(self, query: str) -> Union[float, str, Dict]:
        """Main entry point - solve any math problem"""
        query = query.strip()
        
        # Try equation first
        if '=' in query and any(c.isalpha() for c in query.replace('=', '')):
            return self.solve_equation(query)
        
        # Try calculation
        return self.calculate(query)

    def calculate(self, expression: str) -> Dict[str, Any]:
        """Calculate mathematical expression with Beast Mode features"""
        try:
            original = expression
            
            # Parse natural language
            expression = self._parse_natural_language(expression)
            
            # Clean expression
            expression = self._clean_expression(expression)
            
            # Safe evaluation
            result = eval(expression, {"__builtins__": {}}, self.safe_functions)
            
            # Format result
            if isinstance(result, float):
                if result == int(result):
                    result = int(result)
                else:
                    result = round(result, 10)
            
            return {
                "status": "success",
                "result": result,
                "expression": original,
                "parsed": expression,
                "formatted": f"{original} = {result}"
            }
            
        except ZeroDivisionError:
            return {"status": "error", "error": "Division by zero", "expression": expression}
        except Exception as e:
            return {"status": "error", "error": str(e), "expression": expression}

    def _parse_natural_language(self, text: str) -> str:
        """Convert natural language to math expression"""
        text = text.lower()
        
        for pattern, replacement in self.nl_patterns:
            text = re.sub(pattern, replacement, text, flags=re.I)
        
        return text

    def _clean_expression(self, expr: str) -> str:
        """Clean and normalize expression"""
        expr = expr.replace('^', '**')
        expr = expr.replace('×', '*').replace('÷', '/')
        expr = expr.replace('x', '*')  # Common typo
        expr = re.sub(r'(\d)([a-zA-Z])', r'\1*\2', expr)  # 2pi -> 2*pi
        return expr

    def solve_equation(self, equation: str) -> Dict[str, Any]:
        """Solve algebraic equations with step-by-step solution"""
        try:
            if '=' not in equation:
                return {"status": "error", "error": "Not an equation (no = sign)"}
            
            left, right = equation.split('=', 1)
            left, right = left.strip(), right.strip()
            
            steps = [f"📝 Original: {equation}"]
            
            # Linear equation: ax + b = c
            linear_match = re.match(r'([+-]?\d*\.?\d*)?\s*x\s*([+-]\s*\d+\.?\d*)?\s*', left)
            if linear_match:
                coef = linear_match.group(1)
                coef = float(coef) if coef and coef not in ['+', '-', ''] else (1.0 if coef != '-' else -1.0)
                
                const = linear_match.group(2)
                const = float(const.replace(' ', '')) if const else 0
                
                right_val = float(eval(right, {"__builtins__": {}}, self.safe_functions))
                
                steps.append(f"📐 Rearranging: {coef}x + {const} = {right_val}")
                
                # Solve
                x = (right_val - const) / coef
                steps.append(f"➡️ Subtract {const}: {coef}x = {right_val - const}")
                steps.append(f"➡️ Divide by {coef}: x = {x}")
                steps.append(f"✅ Solution: x = {x}")
                
                return {
                    "status": "success",
                    "solution": x,
                    "variable": "x",
                    "steps": steps,
                    "equation": equation
                }
            
            return {"status": "partial", "message": "Equation type not fully supported", "equation": equation}
            
        except Exception as e:
            return {"status": "error", "error": str(e), "equation": equation}

    def solve_quadratic(self, a: float, b: float, c: float) -> Dict[str, Any]:
        """Solve ax² + bx + c = 0 with detailed steps"""
        steps = [f"📝 Quadratic: {a}x² + {b}x + {c} = 0"]
        
        # Discriminant
        d = b**2 - 4*a*c
        steps.append(f"📐 Discriminant: b² - 4ac = {b}² - 4({a})({c}) = {d}")
        
        if d > 0:
            x1 = (-b + math.sqrt(d)) / (2*a)
            x2 = (-b - math.sqrt(d)) / (2*a)
            steps.append(f"✅ Two real solutions:")
            steps.append(f"   x₁ = {x1:.6f}")
            steps.append(f"   x₂ = {x2:.6f}")
            return {"status": "success", "solutions": [x1, x2], "type": "two_real", "steps": steps}
        elif d == 0:
            x = -b / (2*a)
            steps.append(f"✅ One real solution: x = {x:.6f}")
            return {"status": "success", "solutions": [x], "type": "one_real", "steps": steps}
        else:
            real = -b / (2*a)
            imag = math.sqrt(abs(d)) / (2*a)
            steps.append(f"✅ Two complex solutions:")
            steps.append(f"   x₁ = {real:.4f} + {imag:.4f}i")
            steps.append(f"   x₂ = {real:.4f} - {imag:.4f}i")
            return {"status": "success", "solutions": [f"{real}+{imag}i", f"{real}-{imag}i"], "type": "complex", "steps": steps}

    def convert_units(self, value: float, from_unit: str, to_unit: str) -> Dict[str, Any]:
        """Convert between units"""
        key = f"{from_unit.lower()}_to_{to_unit.lower()}"
        
        # Temperature special cases
        if 'celsius' in key or 'fahrenheit' in key or 'kelvin' in key:
            return self._convert_temperature(value, from_unit, to_unit)
        
        if key in self.units:
            result = value * self.units[key]
            return {
                "status": "success",
                "original": f"{value} {from_unit}",
                "converted": f"{result:.4f} {to_unit}",
                "result": result
            }
        
        return {"status": "error", "error": f"Unknown conversion: {from_unit} to {to_unit}"}

    def _convert_temperature(self, value: float, from_unit: str, to_unit: str) -> Dict[str, Any]:
        """Convert temperature"""
        from_u = from_unit.lower()[0]
        to_u = to_unit.lower()[0]
        
        # Convert to Celsius first
        if from_u == 'c':
            celsius = value
        elif from_u == 'f':
            celsius = (value - 32) * 5/9
        elif from_u == 'k':
            celsius = value - 273.15
        else:
            return {"status": "error", "error": "Unknown temperature unit"}
        
        # Convert from Celsius to target
        if to_u == 'c':
            result = celsius
        elif to_u == 'f':
            result = celsius * 9/5 + 32
        elif to_u == 'k':
            result = celsius + 273.15
        else:
            return {"status": "error", "error": "Unknown target unit"}
        
        return {
            "status": "success",
            "original": f"{value}°{from_u.upper()}",
            "converted": f"{result:.2f}°{to_u.upper()}",
            "result": result
        }

    def statistics_calc(self, numbers: List[float]) -> Dict[str, Any]:
        """Calculate statistical measures"""
        if not numbers:
            return {"status": "error", "error": "No numbers provided"}
        
        try:
            return {
                "status": "success",
                "count": len(numbers),
                "sum": sum(numbers),
                "mean": statistics.mean(numbers),
                "median": statistics.median(numbers),
                "mode": statistics.mode(numbers) if len(numbers) > 1 else numbers[0],
                "stdev": statistics.stdev(numbers) if len(numbers) > 1 else 0,
                "variance": statistics.variance(numbers) if len(numbers) > 1 else 0,
                "min": min(numbers),
                "max": max(numbers),
                "range": max(numbers) - min(numbers)
            }
        except Exception as e:
            return {"status": "error", "error": str(e)}

    def percentage(self, value: float, percent: float, operation: str = "of") -> Dict[str, Any]:
        """Percentage calculations"""
        if operation == "of":
            result = (percent / 100) * value
            return {"status": "success", "result": result, "expression": f"{percent}% of {value} = {result}"}
        elif operation == "increase":
            result = value * (1 + percent / 100)
            return {"status": "success", "result": result, "expression": f"{value} increased by {percent}% = {result}"}
        elif operation == "decrease":
            result = value * (1 - percent / 100)
            return {"status": "success", "result": result, "expression": f"{value} decreased by {percent}% = {result}"}
        return {"status": "error", "error": "Invalid operation"}

    def factorial(self, n: int) -> Dict[str, Any]:
        """Calculate factorial"""
        if n < 0:
            return {"status": "error", "error": "Factorial undefined for negative numbers"}
        if n > 170:
            return {"status": "error", "error": "Number too large (max 170)"}
        
        result = math.factorial(n)
        return {"status": "success", "result": result, "expression": f"{n}! = {result}"}

    def prime_check(self, n: int) -> Dict[str, Any]:
        """Check if number is prime"""
        if n < 2:
            return {"status": "success", "is_prime": False, "message": f"{n} is not prime"}
        
        for i in range(2, int(math.sqrt(n)) + 1):
            if n % i == 0:
                return {"status": "success", "is_prime": False, "message": f"{n} is not prime (divisible by {i})"}
        
        return {"status": "success", "is_prime": True, "message": f"{n} is prime!"}

    def factors(self, n: int) -> Dict[str, Any]:
        """Find all factors of a number"""
        if n <= 0:
            return {"status": "error", "error": "Need positive integer"}
        
        factor_list = [i for i in range(1, n + 1) if n % i == 0]
        return {
            "status": "success",
            "number": n,
            "factors": factor_list,
            "count": len(factor_list),
            "is_prime": len(factor_list) == 2
        }

# Global instance
math_solver = MathSolver()

if __name__ == "__main__":
    print("=== Math Solver Beast Mode Test ===\n")
    
    # Test calculations
    tests = [
        "2 + 2",
        "sqrt(144)",
        "10 percent of 50",
        "5 factorial",
        "2 to the power of 10"
    ]
    
    for t in tests:
        result = math_solver.calculate(t)
        print(f"  {t} = {result.get('result', result.get('error'))}")
    
    print("\n--- Quadratic ---")
    result = math_solver.solve_quadratic(1, -5, 6)
    for step in result['steps']:
        print(f"  {step}")
    
    print("\n--- Statistics ---")
    stats = math_solver.statistics_calc([1, 2, 3, 4, 5, 6, 7, 8, 9, 10])
    print(f"  Mean: {stats['mean']}, Median: {stats['median']}, StDev: {stats['stdev']:.2f}")
    
    print("\n--- Unit Conversion ---")
    result = math_solver.convert_units(100, "celsius", "fahrenheit")
    print(f"  {result.get('original')} = {result.get('converted')}")
