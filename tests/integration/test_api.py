"""
Test script for POORNASREE AI Platform API endpoints
"""
import asyncio
import httpx
import json
import logging
from typing import Dict, Any

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# API base URL
BASE_URL = "http://localhost:8000"
API_URL = f"{BASE_URL}/v1"


class APITester:
    """API testing class"""
    
    def __init__(self):
        self.client = httpx.AsyncClient(timeout=30.0)
        self.tokens: Dict[str, str] = {}
    
    async def test_health_check(self):
        """Test health check endpoint"""
        try:
            response = await self.client.get(f"{BASE_URL}/health")
            logger.info(f"Health Check - Status: {response.status_code}")
            logger.info(f"Health Check - Response: {response.json()}")
            return response.status_code == 200
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return False
    
    async def test_root_endpoint(self):
        """Test root endpoint"""
        try:
            response = await self.client.get(BASE_URL)
            logger.info(f"Root Endpoint - Status: {response.status_code}")
            logger.info(f"Root Endpoint - Response: {response.json()}")
            return response.status_code == 200
        except Exception as e:
            logger.error(f"Root endpoint test failed: {e}")
            return False
    
    async def test_admin_login_step1(self):
        """Test admin login step 1 - send OTP"""
        try:
            payload = {
                "email": "info.pydart@gmail.com"
            }
            
            response = await self.client.post(
                f"{API_URL}/auth/admin/login",
                json=payload
            )
            
            logger.info(f"Admin Login Step 1 - Status: {response.status_code}")
            logger.info(f"Admin Login Step 1 - Response: {response.json()}")
            
            if response.status_code == 200:
                logger.info("✅ OTP should be sent to admin email")
                return True
            else:
                logger.error("❌ Admin login step 1 failed")
                return False
                
        except Exception as e:
            logger.error(f"Admin login step 1 failed: {e}")
            return False
    
    async def test_engineer_registration(self):
        """Test engineer registration"""
        try:
            payload = {
                "email": "test.engineer@example.com",
                "full_name": "Test Engineer",
                "phone_number": "+1234567890",
                "password": "testpassword123",
                "company_name": "Test Company",
                "job_title": "Senior Maintenance Engineer",
                "department": "Operations",
                "experience_years": 5,
                "certifications": ["Certified Maintenance Professional"],
                "expertise_areas": ["Industrial Machinery", "Preventive Maintenance"],
                "employee_id": "ENG001",
                "manager_email": "manager@example.com",
                "additional_info": "Test engineer registration"
            }
            
            response = await self.client.post(
                f"{API_URL}/auth/engineer/register",
                json=payload
            )
            
            logger.info(f"Engineer Registration - Status: {response.status_code}")
            logger.info(f"Engineer Registration - Response: {response.json()}")
            
            if response.status_code == 200:
                logger.info("✅ Engineer registration successful")
                return True
            else:
                logger.error("❌ Engineer registration failed")
                return False
                
        except Exception as e:
            logger.error(f"Engineer registration failed: {e}")
            return False
    
    async def test_invalid_login(self):
        """Test invalid login attempt"""
        try:
            payload = {
                "email": "invalid@example.com",
                "password": "wrongpassword"
            }
            
            response = await self.client.post(
                f"{API_URL}/auth/login",
                json=payload
            )
            
            logger.info(f"Invalid Login - Status: {response.status_code}")
            logger.info(f"Invalid Login - Response: {response.json()}")
            
            # Should return 401 for invalid credentials
            if response.status_code == 401:
                logger.info("✅ Invalid login correctly rejected")
                return True
            else:
                logger.error("❌ Invalid login should return 401")
                return False
                
        except Exception as e:
            logger.error(f"Invalid login test failed: {e}")
            return False
    
    async def test_protected_endpoint_without_token(self):
        """Test accessing protected endpoint without token"""
        try:
            response = await self.client.get(f"{API_URL}/auth/me")
            
            logger.info(f"Protected Endpoint (No Token) - Status: {response.status_code}")
            logger.info(f"Protected Endpoint (No Token) - Response: {response.json()}")
            
            # Should return 403 or 401 for missing token
            if response.status_code in [401, 403]:
                logger.info("✅ Protected endpoint correctly requires authentication")
                return True
            else:
                logger.error("❌ Protected endpoint should require authentication")
                return False
                
        except Exception as e:
            logger.error(f"Protected endpoint test failed: {e}")
            return False
    
    async def test_invalid_token(self):
        """Test using invalid JWT token"""
        try:
            headers = {
                "Authorization": "Bearer invalid_token_here"
            }
            
            response = await self.client.get(
                f"{API_URL}/auth/me",
                headers=headers
            )
            
            logger.info(f"Invalid Token - Status: {response.status_code}")
            logger.info(f"Invalid Token - Response: {response.json()}")
            
            # Should return 401 for invalid token
            if response.status_code == 401:
                logger.info("✅ Invalid token correctly rejected")
                return True
            else:
                logger.error("❌ Invalid token should return 401")
                return False
                
        except Exception as e:
            logger.error(f"Invalid token test failed: {e}")
            return False
    
    async def run_all_tests(self):
        """Run all API tests"""
        logger.info("🚀 Starting POORNASREE AI Platform API Tests...")
        logger.info("=" * 60)
        
        tests = [
            ("Health Check", self.test_health_check),
            ("Root Endpoint", self.test_root_endpoint),
            ("Admin Login Step 1", self.test_admin_login_step1),
            ("Engineer Registration", self.test_engineer_registration),
            ("Invalid Login", self.test_invalid_login),
            ("Protected Endpoint (No Token)", self.test_protected_endpoint_without_token),
            ("Invalid Token", self.test_invalid_token),
        ]
        
        results = []
        
        for test_name, test_func in tests:
            logger.info(f"\n🧪 Running: {test_name}")
            logger.info("-" * 40)
            
            try:
                result = await test_func()
                results.append((test_name, result))
                
                if result:
                    logger.info(f"✅ {test_name} - PASSED")
                else:
                    logger.error(f"❌ {test_name} - FAILED")
                    
            except Exception as e:
                logger.error(f"❌ {test_name} - ERROR: {e}")
                results.append((test_name, False))
        
        # Summary
        logger.info("\n" + "=" * 60)
        logger.info("📊 TEST SUMMARY")
        logger.info("=" * 60)
        
        passed = sum(1 for _, result in results if result)
        total = len(results)
        
        for test_name, result in results:
            status = "✅ PASSED" if result else "❌ FAILED"
            logger.info(f"{test_name}: {status}")
        
        logger.info(f"\nResults: {passed}/{total} tests passed")
        
        if passed == total:
            logger.info("🎉 All tests passed! API is working correctly.")
        else:
            logger.warning(f"⚠️  {total - passed} test(s) failed. Please check the issues above.")
        
        await self.client.aclose()
        return passed == total


async def main():
    """Main test function"""
    tester = APITester()
    success = await tester.run_all_tests()
    
    if success:
        logger.info("\n🎯 Next steps:")
        logger.info("1. Test the OTP verification with a real OTP from email")
        logger.info("2. Create additional endpoints for query processing")
        logger.info("3. Implement document upload and training features")
        logger.info("4. Add analytics and monitoring endpoints")
    else:
        logger.error("\n❌ Please fix the failing tests before proceeding")


if __name__ == "__main__":
    asyncio.run(main())
