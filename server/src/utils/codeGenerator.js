import { PrismaClient } from '@prisma/client';

const prisma = new PrismaClient();

export const generateCode = async (type) => {
  let code;
  let isUnique = false;
  
  while (!isUnique) {
    // Generate 6-digit code
    code = Math.floor(100000 + Math.random() * 900000).toString();
    
    // Check if code is unique
    if (type === 'DENTIST') {
      const existing = await prisma.dentistProfile.findUnique({
        where: { dentistCode: code }
      });
      isUnique = !existing;
    } else if (type === 'SPECIALIST') {
      const existing = await prisma.specialistProfile.findUnique({
        where: { specialistCode: code }
      });
      isUnique = !existing;
    }
  }
  
  return code;
};

export const generateReferralNumber = async () => {
  let referralNumber;
  let isUnique = false;
  
  while (!isUnique) {
    // Generate referral number with format: REF-YYYYMMDD-XXXX
    const date = new Date().toISOString().slice(0, 10).replace(/-/g, '');
    const random = Math.floor(1000 + Math.random() * 9000);
    referralNumber = `REF-${date}-${random}`;
    
    const existing = await prisma.referral.findUnique({
      where: { referralNumber }
    });
    isUnique = !existing;
  }
  
  return referralNumber;
};