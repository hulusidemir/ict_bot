import TradesTable from '../components/TradesTable';

export default function Trades() {
  return (
    <div>
      <h2 className="text-white font-semibold text-xl mb-4">Simüle İşlemler</h2>
      <div className="bg-dark-700 rounded-lg border border-dark-600 p-4">
        <TradesTable />
      </div>
    </div>
  );
}
