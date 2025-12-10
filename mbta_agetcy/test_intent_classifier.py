# test_intent_classifier.py

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from exchange_agent.intent_classifier import create_intent_classifier
import time

def test_intent_classifier():
    """Test the OpenAI embedding-based intent classifier."""
    
    print("🧪 Testing OpenAI Embedding Intent Classifier\n")
    print("=" * 60)
    
    classifier = create_intent_classifier()
    
    test_cases = [
        # High confidence cases
        ("hello", ["general"], 0.80),
        ("are there delays on the red line", ["alerts"], 0.70),
        ("how do I get to Harvard", ["trip_planning"], 0.70),
        ("find stops near Fenway", ["stop_info"], 0.70),
        ("when is the next train", ["schedule"], 0.70),
        
        # Multi-intent cases
        ("any delays and what stops are nearby", ["alerts", "stop_info"], 0.60),
        ("route to South Station and current alerts", ["trip_planning", "alerts"], 0.60),
        
        # Edge cases
        ("what's up", ["general"], 0.50),
        ("show me everything about the red line", None, 0.50),  # Multiple possible intents
    ]
    
    passed = 0
    failed = 0
    total_time = 0
    
    for i, (query, expected_intents, min_confidence) in enumerate(test_cases, 1):
        start = time.time()
        intents, confidences = classifier.classify_intent(query)
        elapsed = (time.time() - start) * 1000
        total_time += elapsed
        
        print(f"\n{'Test ' + str(i)}")
        print(f"Query: '{query}'")
        print(f"Detected: {classifier.get_intent_summary(intents, confidences)}")
        print(f"Time: {elapsed:.1f}ms")
        
        # Check if expected intents are present
        if expected_intents:
            matches = all(intent in intents for intent in expected_intents)
            conf_ok = all(confidences.get(intent, 0) >= min_confidence for intent in expected_intents)
            
            if matches and conf_ok:
                print("✅ PASS")
                passed += 1
            else:
                print(f"❌ FAIL - Expected {expected_intents} with confidence >= {min_confidence}")
                failed += 1
        else:
            # Edge case - just check it didn't crash
            print("✅ PASS (edge case)")
            passed += 1
    
    print(f"\n{'=' * 60}")
    print(f"Results: {passed}/{passed + failed} passed")
    print(f"Average latency: {total_time / len(test_cases):.1f}ms")
    print(f"{'=' * 60}\n")
    
    return passed == len(test_cases)


if __name__ == "__main__":
    success = test_intent_classifier()
    sys.exit(0 if success else 1)