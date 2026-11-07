using System;
using System.Security.Cryptography;
using System.Text;

namespace WebsiteApp
{
    public sealed class PasswordRecord
    {
        public string Salt { get; set; }
        public string Hash { get; set; }
        public int Iterations { get; set; }
    }

    public static class ExitProtection
    {
        public static bool Verify(string password, PasswordRecord record)
        {
            if (record == null) return true;
            if (record.Iterations < 100000 || record.Iterations > 2000000) return false;
            try
            {
                byte[] expected = Convert.FromBase64String(record.Hash);
                byte[] salt = Convert.FromBase64String(record.Salt);
                if (expected.Length != 32 || salt.Length != 16) return false;
                using (var derive = new Rfc2898DeriveBytes(Encoding.UTF8.GetBytes(password), salt,
                    record.Iterations, HashAlgorithmName.SHA256))
                {
                    byte[] actual = derive.GetBytes(32);
                    int difference = 0;
                    for (int i = 0; i < expected.Length; ++i) difference |= expected[i] ^ actual[i];
                    Array.Clear(actual, 0, actual.Length);
                    return difference == 0;
                }
            }
            catch (FormatException) { return false; }
            catch (ArgumentException) { return false; }
        }
    }
}
