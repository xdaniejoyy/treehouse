import pandas as pd


class EmployeeData():
    """Employee data takes in a DataFrame of information.
    Columns: id, Name, Salary, manager_id.

    :param data: DataFrame, employee data
    """

    def __init__(self, data):
        self.data = data

        columns = ['id', 'Name', 'Salary', 'manager_id']
        if any(x not in self.data.columns for x in columns):
            raise ValueError(f"Required columns: {columns}")

        self.data['id'] = self.data['id'].apply(lambda x: int(x))
        self.data['manager_id'] = self.data['manager_id'].apply(
            lambda x: int(x) if pd.notnull(x) else x)
        self.data.set_index('id', inplace=True)

    def get_names_salary_greater_than_mgr(self):
        """
        Return names of employees with salary greater than manager.
        :return: df
        """

        return self.data['Name'][self.data.apply(
            lambda x: x['Salary'] > self.data.loc[x['manager_id'], 'Salary']
            if pd.notnull(x['manager_id']) else False, axis=1).values].tolist()

    def get_avg_salary_non_mgrs(self):
        """
        Return average salary of non-managers.
        :return: float
        """

        return self.data.loc[
            list(set(self.data.index) - set(self.data['manager_id'])),
            'Salary'].mean()



df = pd.DataFrame([
    [1, 'John', 300, 3],
    [2, 'Mike', 200, 3],
    [3, 'Sally', 550, 4],
    [4, 'Jane', 500, 7],
    [5, 'Joe', 600, 7],
    [6, 'Dan', 600, 3],
    [7, 'Phil', 550, None]
], columns=['id', 'Name', 'Salary', 'manager_id'])


q1 = EmployeeData(df)
print(q1.get_names_salary_greater_than_mgr())
print(q1.get_avg_salary_non_mgrs())