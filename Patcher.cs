using System;
using System.Diagnostics;
using System.IO;
using System.Security.Cryptography;
using System.Text;
using System.Threading.Tasks;

class Program
{
    static string GetSha256(string path)
    {
        using (SHA256 sha256 = SHA256.Create())
        using (FileStream stream = File.OpenRead(path))
            return BitConverter.ToString(sha256.ComputeHash(stream)).Replace("-", "").ToLowerInvariant();
    }

    static void Patch(string[] args)
    {
        string basePath = AppDomain.CurrentDomain.BaseDirectory;
        string original = Path.GetFullPath(args.Length > 0 ? args[0] : Path.Combine(basePath, "original.nds"));
        string output = Path.GetFullPath(Path.Combine(basePath, "rei.nds"));
        string patch = Path.Combine(basePath, "korean_patch_v6.dat");
        string xdelta = Path.Combine(basePath, "xdelta3.exe");
        // Reject before opening any output. Never overwrite the input ROM.
        if (string.Equals(original, output, StringComparison.OrdinalIgnoreCase))
            throw new IOException("입력 ROM과 결과 ROM 경로가 같습니다. 원본을 다른 이름/폴더로 옮겨 주세요.");
        if (!File.Exists(original))
            throw new FileNotFoundException("원본 ROM이 없습니다. original.nds를 패처 폴더에 넣거나 ROM을 실행 파일로 끌어 놓으세요.");
        if (!File.Exists(xdelta) || !File.Exists(patch))
            throw new FileNotFoundException("패처 폴더에 xdelta3.exe와 korean_patch_v6.dat가 모두 필요합니다.");

        Console.WriteLine("원본 ROM을 확인합니다...");
        if (!string.Equals(GetSha256(original), PatchManifest.ExpectedSourceSha256, StringComparison.OrdinalIgnoreCase))
            throw new InvalidDataException("지원하지 않거나 변경된 원본 ROM입니다. 원본 파일은 변경하지 않았습니다.");
        Console.Write("PIN: ");
        string pin = Console.ReadLine();
        if (string.IsNullOrEmpty(pin))
            throw new InvalidDataException("PIN이 입력되지 않았습니다.");

        byte[] patchData = File.ReadAllBytes(patch);
        if (patchData.Length <= 16 || (patchData.Length - 16) % 16 != 0)
            throw new InvalidDataException("패치 데이터가 손상됐습니다. 배포 ZIP을 다시 풀어 주세요.");
        byte[] decryptedPatch;
        using (SHA256 sha256 = SHA256.Create())
        using (AesCryptoServiceProvider aes = new AesCryptoServiceProvider())
        {
            aes.Key = sha256.ComputeHash(Encoding.UTF8.GetBytes(pin));
            byte[] iv = new byte[16];
            Array.Copy(patchData, iv, iv.Length);
            aes.IV = iv;
            aes.Mode = CipherMode.CBC;
            aes.Padding = PaddingMode.PKCS7;
            using (ICryptoTransform decryptor = aes.CreateDecryptor())
                decryptedPatch = decryptor.TransformFinalBlock(patchData, 16, patchData.Length - 16);
        }

        string temporary = output + "." + Guid.NewGuid().ToString("N") + ".tmp";
        try
        {
            Console.WriteLine("패치를 적용합니다... (기존 결과물은 검증 완료까지 보존됩니다)");
            ProcessStartInfo psi = new ProcessStartInfo();
            psi.FileName = xdelta;
            psi.WorkingDirectory = basePath;
            psi.Arguments = string.Format("-d -c -s \"{0}\"", original);
            psi.UseShellExecute = false;
            psi.RedirectStandardInput = true;
            psi.RedirectStandardOutput = true;
            psi.RedirectStandardError = true;
            psi.CreateNoWindow = true;
            using (FileStream stream = new FileStream(temporary, FileMode.CreateNew, FileAccess.Write))
            using (Process process = Process.Start(psi))
            {
                Task<string> errorTask = Task.Run(() => process.StandardError.ReadToEnd());
                Task writeTask = Task.Run(() =>
                {
                    try { process.StandardInput.BaseStream.Write(decryptedPatch, 0, decryptedPatch.Length); }
                    finally { process.StandardInput.Close(); }
                });
                try
                {
                    process.StandardOutput.BaseStream.CopyTo(stream);
                    process.WaitForExit();
                    string error = errorTask.Result;
                    Exception writeError = null;
                    try { writeTask.Wait(); } catch (AggregateException ex) { writeError = ex.GetBaseException(); }
                    if (process.ExitCode != 0)
                        throw new InvalidDataException("패치 적용 실패: " + error.Trim());
                    if (writeError != null) throw new IOException("패치 데이터 전송 실패", writeError);
                    stream.Flush(true);
                }
                finally
                {
                    if (!process.HasExited) process.Kill();
                    process.WaitForExit();
                    try { writeTask.Wait(); } catch (AggregateException) { }
                    errorTask.Wait();
                }
            }
            if (!string.Equals(GetSha256(temporary), PatchManifest.ExpectedTargetSha256, StringComparison.OrdinalIgnoreCase))
                throw new InvalidDataException("결과 ROM 무결성 검증에 실패했습니다. 기존 결과물은 보존됩니다.");

            if (File.Exists(output)) File.Replace(temporary, output, null);
            else File.Move(temporary, output);
            Console.WriteLine("패치 및 SHA-256 검증 완료!\n결과: " + output);
        }
        finally
        {
            try { if (File.Exists(temporary)) File.Delete(temporary); }
            catch { /* Preserve the original error if cleanup also fails. */ }
        }
    }

    static void Main(string[] args)
    {
        Console.OutputEncoding = Encoding.UTF8;
        Console.WriteLine("레육계 DS 한글 패치 by hanbi\n");
        try { Patch(args); }
        catch (CryptographicException)
        {
            Console.WriteLine("오류: PIN이 틀렸거나 패치 데이터가 손상됐습니다.");
            Environment.ExitCode = 1;
        }
        catch (Exception ex)
        {
            Console.WriteLine("오류: " + ex.Message);
            Environment.ExitCode = 1;
        }
        Console.WriteLine("\nEnter를 누르면 종료합니다.");
        Console.ReadLine();
    }
}
